"""
Show the alignment of a sequence in a map.
"""

from pymsaviz import MsaViz
import pandas as pd
from ..utils.fileio import write_a3m, encode_a3m
from ..utils.msatools import unify_length

import matplotlib.pyplot as plt
from uuid import uuid4
from pathlib import Path

from dash import Dash
from dash_bio import AlignmentChart

max_rows_for_visualisation = 150
"""
Because the plotting with too many rows can crash the plotting
library, we limit the number of rows to include.
Rows are uniformly subsampled by going through the dataframe at a step of len(df) // max_rows_for_visualisation.
"""


def visualise_msa(df: pd.DataFrame, backend: str = "matplotlib"):
    """
    Visualise the MSA of a sequence in a map.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the MSA data. This needs to contain a column named "sequence".
    backend : str
        The backend to use for visualisation. Can be "matplotlib" or "plotly".

    Returns
    -------
    plt.figure or AlignmentChart
        The figure object containing the MSA map.
    """
    if backend == "matplotlib":
        return _maptlotlib_visualise_msa(df)
    elif backend == "plotly":
        return _plotly_visualise_msa(df)
    else:
        raise ValueError("Backend must be 'matplotlib' or 'plotly'.")


def _maptlotlib_visualise_msa(df: pd.DataFrame) -> plt.figure:
    """
    Visualise the MSA of a sequence in a map.

    Args:
        df (pd.DataFrame): DataFrame containing the MSA data.

    Returns:
        plt.figure: The figure object containing the MSA map.
    """
    # Convert the DataFrame to A3M format
    tmpdir = Path("/tmp")
    if not tmpdir.exists():
        tmpdir = Path.cwd()

    tmpfile = tmpdir / f"msa_{uuid4()}.a3m"

    df = df.copy()
    if len(df) > max_rows_for_visualisation:
        print(
            f"Warning: The MSA has more than {max_rows_for_visualisation} sequences which will cause the plot to crash! Downsampling uniformly to 150 sequences."
        )
        df = df.iloc[:: len(df) // max_rows_for_visualisation]
    write_a3m(unify_length(df, "first"), tmpfile)

    # Create an MsaViz object
    msa_viz = MsaViz(str(tmpfile))

    # Create the figure
    fig = msa_viz.plotfig()
    tmpfile.unlink()

    return fig


def _plotly_visualise_msa(df: pd.DataFrame) -> AlignmentChart:
    """
    Visualise the MSA of a sequence in a map using Plotly.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the MSA data. This needs to contain a column named "sequence".

    Returns
    -------
    AlignmentChart
        The Plotly AlignmentChart object containing the MSA map.
    """
    df = df.copy()
    if len(df) > max_rows_for_visualisation:
        print(
            f"Warning: The MSA has more than {max_rows_for_visualisation} sequences which will cause the plot to crash! Downsampling uniformly to 150 sequences."
        )
        df = df.iloc[:: len(df) // max_rows_for_visualisation]

    a3m_string = encode_a3m(unify_length(df, "first"))
    chart = AlignmentChart(
        id="alignment-chart",
        data=a3m_string,
        showlabel=True,
        showid=True,
        showconservation=True,
        showconsensus=False,
        showgap=False,
    )

    return chart
