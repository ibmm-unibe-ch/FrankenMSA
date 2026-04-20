import numpy as np
import pandas as pd

from frankenmsa.visual import conservation_scores
from frankenmsa.visual import gap_counts
from frankenmsa.visual import query_identity_scores


def make_msa() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "header": ["query", "hit1", "hit2"],
            "sequence": ["AC-D", "A--D", "ATGD"],
        }
    )


def test_gap_counts_returns_per_position_series():
    result = gap_counts(make_msa())

    assert result.name == "gap_count"
    assert result.tolist() == [0.0, 1.0, 2.0, 0.0]


def test_conservation_scores_returns_per_position_fraction():
    result = conservation_scores(make_msa())

    assert result.name == "conservation"
    assert np.allclose(result.tolist(), [1.0, 1 / 3, 2 / 3, 1.0])


def test_query_identity_scores_returns_identity_to_query():
    result = query_identity_scores(make_msa())

    assert result.name == "identity"
    assert np.allclose(result.tolist(), [1.0, 0.0, 0.5, 1.0])


def test_query_identity_scores_single_sequence_defaults_to_one():
    msa = pd.DataFrame({"header": ["query"], "sequence": ["ACD"]})

    result = query_identity_scores(msa)

    assert result.tolist() == [1.0, 1.0, 1.0]