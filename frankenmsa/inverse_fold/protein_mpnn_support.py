from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

PROTEINMPNN_ROOT_ENV_VARS = (
    "FRANKENMSA_PROTEINMPNN_ROOT",
    "PROTEINMPNN_LOCAL_ROOT",
    "ProteinMPNN_DIR",
)

PROTEINMPNN_WEIGHTS_DIR_ENV_VARS = (
    "FRANKENMSA_PROTEINMPNN_WEIGHTS_DIR",
    "PROTEINMPNN_WEIGHTS_DIR",
)

PROTEINMPNN_WEIGHTS_ROOT_ENV_VARS = (
    "FRANKENMSA_PROTEINMPNN_WEIGHTS_ROOT",
    "PROTEINMPNN_WEIGHTS_ROOT",
)

PROTEINMPNN_OUT_DIR_ENV_VAR = "PROTEINMPNN_OUT_DIR"


def proteinmpnn_weight_subdir(
    use_soluble_model: bool = False,
    ca_only: bool = False,
) -> str:
    if ca_only:
        return "ca_model_weights"
    if use_soluble_model:
        return "soluble_model_weights"
    return "vanilla_model_weights"


def is_valid_proteinmpnn_root(path: Path | str) -> bool:
    root = _normalize_root_candidate(path)
    return (root / "protein_mpnn_run.py").is_file() and (
        root / "helper_scripts"
    ).is_dir()


def resolve_proteinmpnn_root(custom_root: Optional[str] = None) -> Path:
    for candidate in _root_candidates(custom_root):
        if is_valid_proteinmpnn_root(candidate):
            return _normalize_root_candidate(candidate)

    env_hint = ", ".join(PROTEINMPNN_ROOT_ENV_VARS)
    raise RuntimeError(
        "Could not locate a usable ProteinMPNN checkout. "
        f"Set one of {env_hint} or install ProteinMPNN under the repository root."
    )


def resolve_proteinmpnn_weights(
    repo_root: Path | str,
    use_soluble_model: bool = False,
    ca_only: bool = False,
    override_dir: Optional[str] = None,
) -> Path:
    repo_root = _normalize_root_candidate(repo_root)

    for candidate in _weight_dir_candidates(override_dir):
        if candidate.is_dir():
            return candidate
        raise RuntimeError(f"Weights directory not found: {candidate}")

    subdir = proteinmpnn_weight_subdir(
        use_soluble_model=use_soluble_model,
        ca_only=ca_only,
    )
    for candidate in _weight_root_candidates(repo_root):
        target = candidate / subdir
        if target.is_dir():
            return target

    env_hint = ", ".join(
        PROTEINMPNN_WEIGHTS_DIR_ENV_VARS + PROTEINMPNN_WEIGHTS_ROOT_ENV_VARS
    )
    raise RuntimeError(
        "Unable to locate ProteinMPNN model weights. "
        f"Set one of {env_hint} or install the weights inside the ProteinMPNN checkout."
    )


def resolve_proteinmpnn_out_dir(repo_root: Path | str, default_name: str) -> Path:
    override = os.environ.get(PROTEINMPNN_OUT_DIR_ENV_VAR)
    out_dir = (
        Path(override).expanduser()
        if override
        else _normalize_root_candidate(repo_root) / default_name
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _root_candidates(custom_root: Optional[str]) -> Iterable[Path]:
    repo_root = Path(__file__).resolve().parents[2]
    candidates = []
    if custom_root:
        candidates.append(Path(custom_root).expanduser())

    for env_var in PROTEINMPNN_ROOT_ENV_VARS:
        value = os.environ.get(env_var)
        if value:
            candidates.append(Path(value).expanduser())

    candidates.extend(
        [
            repo_root / "ProteinMPNN",
            Path.cwd() / "ProteinMPNN",
            Path.home() / "ProteinMPNN",
        ]
    )
    return _dedupe_paths(candidates)


def _weight_dir_candidates(override_dir: Optional[str]) -> Iterable[Path]:
    candidates = []
    if override_dir:
        candidates.append(Path(override_dir).expanduser())

    for env_var in PROTEINMPNN_WEIGHTS_DIR_ENV_VARS:
        value = os.environ.get(env_var)
        if value:
            candidates.append(Path(value).expanduser())

    return _dedupe_paths(candidates)


def _weight_root_candidates(repo_root: Path) -> Iterable[Path]:
    candidates = [repo_root]
    for env_var in PROTEINMPNN_WEIGHTS_ROOT_ENV_VARS:
        value = os.environ.get(env_var)
        if value:
            candidates.append(Path(value).expanduser())
    return _dedupe_paths(candidates)


def _normalize_root_candidate(path: Path | str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_file():
        candidate = candidate.parent
    if candidate.name == "protein_mpnn_utils.py":
        candidate = candidate.parent
    nested = candidate / "ProteinMPNN"
    if (candidate / "protein_mpnn_run.py").is_file():
        return candidate
    if (nested / "protein_mpnn_run.py").is_file():
        return nested
    return candidate


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen = set()
    ordered = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(path)
    return ordered
