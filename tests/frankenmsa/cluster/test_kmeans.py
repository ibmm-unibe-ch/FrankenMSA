import pandas as pd
import numpy as np
from pathlib import Path

PARENT = Path(__file__).parent
FILES = PARENT.parents[1] / "files"

TEST_MSA1 = FILES / "test1.a3m"


def test_kmeans():
    from frankenmsa.utils import read_a3m
    from frankenmsa.cluster import kmeans

    msa = read_a3m(TEST_MSA1)
    assert isinstance(msa, pd.DataFrame)
    assert "sequence" in msa.columns
    assert "header" in msa.columns
    assert len(msa) > 1

    clustered_msa = kmeans(msa, n_clusters=5)
    assert isinstance(clustered_msa, pd.DataFrame)
    assert "sequence" in clustered_msa.columns
    assert "header" in clustered_msa.columns
    assert "cluster_id" in clustered_msa.columns


def test_kmeans_with_additional_columns():
    from frankenmsa.utils import read_a3m
    from frankenmsa.cluster import kmeans

    msa = read_a3m(TEST_MSA1)
    assert isinstance(msa, pd.DataFrame)
    assert "sequence" in msa.columns
    assert "header" in msa.columns
    assert len(msa) > 1

    # Add an additional column to the MSA DataFrame
    msa["additional_column"] = np.random.rand(len(msa))
    assert "additional_column" in msa.columns

    msa["categorical_column"] = np.random.choice([0, 1, 2], len(msa))

    clustered_msa = kmeans(
        msa, n_clusters=5, columns=["additional_column", "categorical_column"]
    )
    assert isinstance(clustered_msa, pd.DataFrame)
    assert "sequence" in clustered_msa.columns
    assert "header" in clustered_msa.columns
    assert "cluster_id" in clustered_msa.columns
