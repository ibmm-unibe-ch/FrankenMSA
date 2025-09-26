import pandas as pd
from frankenmsa.utils.msatools import shuffle_msa, unify_length

def make_test_df():
    # Toy MSA: row 0 is the query (must stay unchanged)
    return pd.DataFrame({
        "sequence": [
            "ACGT",   # query
            "AGGT",
            "ATGT",
            "AC-T",
        ]
    })

def test_shuffle_query_fixed_and_changes():
    df = make_test_df()
    df = unify_length(df, "first")

    shuffled = shuffle_msa(df, preserve_gaps=True, random_state=42)

    # 1) Query (row 0) must be identical
    assert shuffled["sequence"].iloc[0] == df["sequence"].iloc[0]

    # 2) At least one non-query row must change
    changed = any(
        shuffled["sequence"].iloc[i] != df["sequence"].iloc[i]
        for i in range(1, len(df))
    )
    assert changed

def test_shuffle_preserve_gaps_true():
    df = make_test_df()
    df = unify_length(df, "first")

    shuffled = shuffle_msa(df, preserve_gaps=True, random_state=42)

    # If a non-query row had a gap in a column, it must remain a gap after shuffling
    L = df["sequence"].str.len().iloc[0]
    for col in range(L):
        for row in range(1, len(df)):
            if df["sequence"].iloc[row][col] == "-":
                assert shuffled["sequence"].iloc[row][col] == "-"

def test_shuffle_preserve_gaps_false():
    df = make_test_df()
    df = unify_length(df, "first")

    shuffled = shuffle_msa(df, preserve_gaps=False, random_state=42)

    # Query stays identical
    assert shuffled["sequence"].iloc[0] == df["sequence"].iloc[0]

    # At least one non-query row changed
    changed = any(
        shuffled["sequence"].iloc[i] != df["sequence"].iloc[i]
        for i in range(1, len(df))
    )
    assert changed

def test_shuffle_with_range():
    df = make_test_df()
    df = unify_length(df, "first")

    shuffled = shuffle_msa(df, start=1, end=3, preserve_gaps=True, random_state=42)

    # Query stays identical
    assert shuffled["sequence"].iloc[0] == df["sequence"].iloc[0]

    # Some non-query row changed
    changed = any(
        shuffled["sequence"].iloc[i] != df["sequence"].iloc[i]
        for i in range(1, len(df))
    )
    assert changed

    # Columns outside [1,3) must be unchanged (col 0 and col 3)
    for col in [0, 3]:
        for row in range(len(df)):
            assert shuffled["sequence"].iloc[row][col] == df["sequence"].iloc[row][col]