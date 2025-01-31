"""
Bindings for HH-suite
"""

from pathlib import Path
import subprocess

HHFILTER_PATH = "hhfilter"


def has_hhsuite() -> bool:
    """
    Check if HH-suite is installed.

    Returns
    -------
    bool
        True if HH-suite is installed, False otherwise.
    """
    try:
        out = subprocess.run(
            [HHFILTER_PATH, "-h"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if out.returncode != 0:
            return False
        return True
    except FileNotFoundError:
        return False


def hhfilter(
    input_file: str,
    diff: int,
    max_pairwise_identity: int = 100,
    min_query_coverage: int = 50,
    min_query_identity: int = 0,
    min_query_score: float = -20,
    target_diversity: int = 0,
    output_file: str = None,
    *args,
    **kwargs,
) -> str:
    """
    Filter an MSA using HH-suite's hhfilter.

    Parameters
    ----------
    input_file : str
        Path to the input MSA file.
    diff : int
        Sequence diversity factor. Minimum sequences to retain in the MSA (option -diff).
    max_pairwise_identity : int, optional
        Maximum pairwise identity, by default 100 (option -id).
    min_query_coverage : int, optional
        Minimum query coverage, by default 50 (option -cov).
    min_query_identity : int, optional
        Minimum query identity, by default 0 (option -qid).
    min_query_score : float, optional
        Minimum query score, by default -20 (option -qsc).
    target_diversity : int, optional
        Target diversity, by default 0 = disabled (option -neff).
    output_file : str, optional
        Path to the output MSA file, by default the input filename is appended by 'filtered'.
    *args
        Additional arguments that will be passed to the hhfilter command (dashes are added automatically).
    **kwargs
        Additional keyword arguments that will be passed to the hhfilter command (dashes are added automatically).

    Returns
    -------
    str
        Path to the output MSA file.
    """
    if output_file is None:
        output_file = Path(input_file).with_suffix(
            ".filtered." + Path(input_file).suffix
        )
    kws = {
        "diff": diff,
        "id": max_pairwise_identity,
        "cov": min_query_coverage,
        "qid": min_query_identity,
        "qsc": min_query_score,
        "neff": target_diversity,
    }
    kws.update(kwargs)
    kws_line = " ".join(f"-{k} {v}" for k, v in kws.items())
    kws_line += " " + " ".join(i if i.startswith("-") else f"i{i}" for i in args)
    command = f"{HHFILTER_PATH} {kws_line} -i {input_file} -o {output_file}"
    subprocess.run(command, shell=True, check=True)
    return output_file
