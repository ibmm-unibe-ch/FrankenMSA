from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from ..augment import base
from ..runtime import log_message
from ..utils.fileio import read_a3m, write_a3m


GHOSTFOLD_BIN_ENV_VARS = (
    "FRANKENMSA_GHOSTFOLD_BIN",
    "GHOSTFOLD_BIN",
)
GHOSTFOLD_ROOT_ENV_VARS = (
    "FRANKENMSA_GHOSTFOLD_ROOT",
    "GHOSTFOLD_ROOT",
)
def _iter_ghostfold_commands() -> list[list[str]]:
    commands: list[list[str]] = []

    for env_var in GHOSTFOLD_BIN_ENV_VARS:
        command = os.environ.get(env_var)
        if command:
            commands.append([command])

    for env_var in GHOSTFOLD_ROOT_ENV_VARS:
        root_value = os.environ.get(env_var)
        if not root_value:
            continue
        root = Path(root_value).expanduser()
        for candidate in (root / "ghostfold.sh", root / "ghostfold"):
            if candidate.is_file():
                commands.append([str(candidate)])

    resolved_cli = shutil.which("ghostfold")
    if resolved_cli:
        commands.append([resolved_cli])

    # Fallback: look for a ghostfold checkout relative to the current working
    # directory (matches the default clone location used by install_ghostfold.py)
    cwd_script = Path.cwd() / "ghostfold" / "ghostfold.sh"
    if cwd_script.is_file():
        commands.append([str(cwd_script)])

    deduped: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for command in commands:
        key = tuple(command)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(command)

    return deduped


def resolve_ghostfold_command() -> list[str]:
    commands = _iter_ghostfold_commands()
    if commands:
        return commands[0]

    raise FileNotFoundError(
        "GhostFold executable not found. Install it with "
        "`python scripts/installers/install_ghostfold.py` or set one of "
        f"{', '.join(GHOSTFOLD_BIN_ENV_VARS + GHOSTFOLD_ROOT_ENV_VARS)}."
    )


def _build_ghostfold_command(fasta_path: Path, project_name: str) -> list[str]:
    command = resolve_ghostfold_command()
    executable_name = Path(command[0]).name

    if executable_name == "ghostfold.sh":
        return command + [
            "--project_name",
            project_name,
            "--fasta_file",
            str(fasta_path),
            "--msa-only",
        ]

    return command + [
        "msa",
        "--project-name",
        project_name,
        "--fasta-path",
        str(fasta_path),
    ]


def _find_ghostfold_output(project_dir: Path) -> Path:
    for pattern in ("msa/*/pstMSA.a3m", "msa/*/pstMSA.fasta"):
        matches = sorted(project_dir.glob(pattern))
        if matches:
            return matches[0]

    raise FileNotFoundError(
        f"GhostFold did not produce a pseudoMSA under {project_dir / 'msa'}."
    )


class GhostFold(base.AugmentationFactory):
    """
    Augmentation method that uses GhostFold to generate new sequences.
    """

    def augment(self, sequence):
        """
        Augment sequences using GhostFold.

        Parameters
        ----------
        sequence : str
            Input sequence to augment.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the augmented sequences.
        """
        jobname = "ghostfold_job"
        log_message(f"Running GhostFold augmentation for input sequence: {sequence}")

        with tempfile.TemporaryDirectory(prefix="frankenmsa-ghostfold-") as tmp_dir:
            work_dir = Path(tmp_dir)
            project_name = work_dir.name
            input_fasta = work_dir / f"{jobname}.fasta"

            write_a3m(
                pd.DataFrame({"header": ["GhostFold_input"], "sequence": [sequence]}),
                str(input_fasta),
            )
            log_message(f"Written GhostFold input FASTA to {input_fasta}.")

            command = _build_ghostfold_command(input_fasta, project_name)
            cwd_path = Path(command[0]).parent
            log_message(f"Running GhostFold command: {' '.join(command)} and cwd: {Path(command[0]).parent}")
            proc = subprocess.run(
                command,
                cwd=cwd_path,
                capture_output=True,
                text=True,
            )

            log_message(f"GhostFold stdout:\n{proc.stdout}")
            log_message(f"GhostFold stderr:\n{proc.stderr}")

            if proc.returncode != 0:
                msg = (
                    f"GhostFold failed with returncode {proc.returncode}. "
                    "Check the FrankenMSA log for stdout/stderr details."
                )
                log_message(msg)
                raise subprocess.CalledProcessError(
                    proc.returncode,
                    proc.args,
                    output=proc.stdout,
                    stderr=proc.stderr,
                )

            output_path = _find_ghostfold_output(cwd_path / project_name)
            log_message(f"Reading GhostFold output from {output_path}.")
            output_df = read_a3m(str(output_path))
            log_message(
                f"GhostFold augmentation completed. Generated {len(output_df)} sequences."
            )
            return output_df
