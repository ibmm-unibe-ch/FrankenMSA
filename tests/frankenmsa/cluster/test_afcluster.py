import pandas as pd
import numpy as np
from pathlib import Path

PARENT = Path(__file__).parent
FILES = PARENT.parents[1] / "files"

TEST_MSA1 = FILES / "test1.a3m"


def test_afcluster():
    from frankenmsa.utils import read_a3m
    from frankenmsa.cluster import afcluster

    msa = read_a3m(TEST_MSA1)
    assert isinstance(msa, pd.DataFrame)
    assert "sequence" in msa.columns
    assert "header" in msa.columns
    assert len(msa) > 1

    clustered_msa = afcluster(msa, eps=8, min_samples=10)
    assert isinstance(clustered_msa, pd.DataFrame)
    assert "sequence" in clustered_msa.columns
    assert "header" in clustered_msa.columns
    assert "cluster_id" in clustered_msa.columns
