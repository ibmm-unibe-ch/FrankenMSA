import pandas as pd

from frankenmsa.utils.msatools import shuffle_rows, sort_by_column


def make_test_df():
    return pd.DataFrame(
        {
            "header": ["query", "hit2", "hit1"],
            "sequence": ["AAAA", "CCCC", "BBBB"],
            "score": [10, 2, 1],
        }
    )


def test_sort_by_column_keeps_query_first():
    df = make_test_df()

    result = sort_by_column(df, "score", ascending=True)

    assert result["header"].tolist() == ["query", "hit1", "hit2"]


def test_sort_by_column_can_sort_all_rows():
    df = make_test_df()

    result = sort_by_column(df, "score", ascending=True, preserve_query=False)

    assert result["header"].tolist() == ["hit1", "hit2", "query"]


def test_shuffle_rows_keeps_query_and_shuffles_rest():
    df = make_test_df()

    result = shuffle_rows(df, random_state=42)

    assert result["header"].iloc[0] == "query"
    assert result["header"].tolist()[1:] == ["hit1", "hit2"]


def test_shuffle_rows_can_shuffle_all_rows():
    df = make_test_df()

    result = shuffle_rows(df, random_state=42, preserve_query=False)

    assert sorted(result["header"].tolist()) == sorted(df["header"].tolist())
