import pandas as pd
import numpy as np
from pathlib import Path

PARENT = Path(__file__).parent
FILES = PARENT.parents[1] / "files"

TEST1_MSA = FILES / "test1.a3m"


def test_can_visualize_msa():
    from frankenmsa.visual import visualize_msa
    from frankenmsa.utils import read_a3m
    import matplotlib.pyplot as plt

    msa = read_a3m(TEST1_MSA)
    assert isinstance(msa, pd.DataFrame)
    assert "sequence" in msa.columns
    assert "header" in msa.columns
    assert len(msa) > 1

    fig = visualize_msa(msa)
    assert fig is not None
    assert isinstance(fig, plt.Figure)
