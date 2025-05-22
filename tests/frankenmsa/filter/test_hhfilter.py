import pandas as pd
import numpy as np
from pathlib import Path

PARENT = Path(__file__).parent
FILES = PARENT.parents[1] / "files"

TEST1_MSA = FILES / "test1.a3m"


def test_hhfilter():
    from frankenmsa.utils import read_a3m
    from frankenmsa.filter import hhfilter

    msa = read_a3m(TEST1_MSA)
    assert isinstance(msa, pd.DataFrame)
    assert "sequence" in msa.columns
    assert "header" in msa.columns
    assert len(msa) > 1

    len_before = len(msa)

    filtered_msa = hhfilter(msa, diff=50)
    assert isinstance(filtered_msa, pd.DataFrame)
    assert "sequence" in filtered_msa.columns
    assert "header" in filtered_msa.columns
    assert len(filtered_msa) < len_before
    assert len(filtered_msa) > 0
