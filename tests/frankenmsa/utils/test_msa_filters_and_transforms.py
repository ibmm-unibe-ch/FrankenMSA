import pandas as pd
import pytest

from frankenmsa.utils.msatools import (
    filter_by_query,
    filter_by_regex,
    lowercase_sequences,
    replace_characters,
    replace_insertions_with_gaps,
    replace_unknown_with_gaps,
    uppercase_sequences,
)


def make_test_df():
    return pd.DataFrame(
        {
            "header": ["query", "hit1", "hit2"],
            "sequence": ["MAAAK", "MccCK", "TTTTX"],
            "score": [1.0, 0.5, 0.1],
        }
    )


def test_filter_by_regex_contains():
    df = make_test_df()

    result = filter_by_regex(df, "AA", method="contains")

    assert result["header"].tolist() == ["query"]


def test_filter_by_regex_match_and_inverse():
    df = make_test_df()

    result = filter_by_regex(df, "^M", method="match", inverse=True)

    assert result["header"].tolist() == ["hit2"]


def test_filter_by_query_uses_pandas_query():
    df = make_test_df()

    result = filter_by_query(df, "score >= 0.5")

    assert result["header"].tolist() == ["query", "hit1"]


def test_replace_insertions_with_gaps_replaces_lowercase_only():
    df = make_test_df()

    result = replace_insertions_with_gaps(df)

    assert result["sequence"].tolist() == ["MAAAK", "M--CK", "TTTTX"]


def test_replace_unknown_with_gaps_replaces_x():
    df = make_test_df()

    result = replace_unknown_with_gaps(df)

    assert result["sequence"].tolist() == ["MAAAK", "MccCK", "TTTT-"]


def test_replace_characters_supports_literal_and_regex_modes():
    df = make_test_df()

    literal = replace_characters(df, "A", "Z", regex=False)
    regex = replace_characters(df, r"[MT]", "_", regex=True)

    assert literal["sequence"].tolist()[0] == "MZZZK"
    assert regex["sequence"].tolist() == ["_AAAK", "_ccCK", "____X"]


def test_case_transforms_change_only_sequence_column():
    df = make_test_df()

    upper = uppercase_sequences(df)
    lower = lowercase_sequences(df)

    assert upper["sequence"].tolist() == ["MAAAK", "MCCCK", "TTTTX"]
    assert lower["sequence"].tolist() == ["maaak", "mccck", "ttttx"]
    assert upper["header"].tolist() == df["header"].tolist()


def test_filter_by_regex_requires_non_empty_pattern():
    df = make_test_df()

    with pytest.raises(ValueError, match="pattern"):
        filter_by_regex(df, "")


def test_filter_by_query_requires_non_empty_query():
    df = make_test_df()

    with pytest.raises(ValueError, match="query_string"):
        filter_by_query(df, "   ")