"""
Bindings for HH-suite
"""

from pathlib import Path
import pandas as pd
import subprocess
import uuid

from ..utils.fileio import read_a3m, write_a3m

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
        df: pd.DataFrame,
        diff: int,
        max_pairwise_identity: int = 100,
        min_query_coverage: int = 50,
        min_query_identity: int = 0,
        min_query_score: float = -20,
        target_diversity: int = 0,
        *args,
        **kwargs,
) -> pd.DataFrame:
    """
    Filter an MSA using HH-suite's hhfilter.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the MSA to filter. This must at least contain the column "sequence".
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
    pd.DataFrame
        DataFrame containing the filtered MSA.
    """
    if not has_hhsuite():
        raise RuntimeError("HH-suite is not installed. Please install it to use this function.")
    
    if "sequence" not in df.columns:
        raise ValueError("The DataFrame must contain a 'sequence' column.")
    
    fname = str(uuid.uuid4())
    input_file = Path(fname + ".a3m")
    output_file = Path(fname + ".filtered.a3m")
    write_a3m(df, input_file)
    output_file = _hhfilter(
        input_file,
        diff,
        max_pairwise_identity,
        min_query_coverage,
        min_query_identity,
        min_query_score,
        target_diversity,
        *args,
        **kwargs,
    )
    _raw_filtered_df = read_a3m(output_file)
    filtered_df = df[df.sequence.isin(_raw_filtered_df.sequence)]
    filtered_df = filtered_df.reset_index(drop=True)
    input_file.unlink(missing_ok=True)
    output_file.unlink(missing_ok=True)
    return filtered_df


def _hhfilter(
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
