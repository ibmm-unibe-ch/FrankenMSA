import pandas as pd
import pytest
from frankenmsa.utils.msatools import (
    replace_at,
    insert_at,
    remove_at,
    fix_at,
)


def make_test_df():
    return pd.DataFrame(
        {
            "sequence": [
                "ACGTACGT",  # query (row 0)
                "AGGTACGT",
                "ATGTACGT",
                "AC-TACGT",
            ]
        }
    )


def test_specify_at():
    """Test specifying a sequence at a given position."""
    df = make_test_df()

    result = replace_at(df, "BBBB", index=3, include_query=False)

    assert result["sequence"].iloc[0] == "ACGTACGT"  # query unchanged
    assert result["sequence"].iloc[1] == "AGGBBBBT"
    assert result["sequence"].iloc[2] == "ATGBBBBT"
    assert result["sequence"].iloc[3] == "AC-BBBBT"

    result = replace_at(result, "CCCC", index=0, include_query=True)
    assert result["sequence"].iloc[0] == "CCCCACGT"
    assert result["sequence"].iloc[1] == "CCCCBBBT"


def test_insert_at():
    """Test inserting a sequence at a given position."""
    df = make_test_df()
    length = len(df["sequence"].iloc[0])
    result = insert_at(df, "TTTTTTTT", index=2, include_query=True)
    assert result["sequence"].iloc[0] == "ACTTTTTTTTGTACGT"
    assert result["sequence"].iloc[1] == "AGTTTTTTTTGTACGT"


def test_remove_slice():
    """Test removing a slice from sequences."""
    df = make_test_df()
    # Remove positions 2 to 5 (removes "GTA")
    result = remove_at(df, start=0, end=2)

    # Check that all sequences have the slice removed
    assert result["sequence"].iloc[0] == "GTACGT"  # ACGTACGT -> CGTACGT
    assert result["sequence"].iloc[3] == "-TACGT"  # AC-TACGT -> AC-CGT


def test_fix_at():
    """Test fixing residues from query sequence at specified positions."""
    df = make_test_df()
    query_seq = df["sequence"].iloc[0]  # ACGTACGT

    # Fix positions 0 and 2 (A and G from query)
    result = fix_at(df, indices=[0, 2])

    # Check that non-query rows have the query residues at the fixed positions
    assert result["sequence"].iloc[1][0] == "A"  # Was 'A', stays 'A'
    assert result["sequence"].iloc[1][2] == "G"  # Was 'G', stays 'G'
    assert result["sequence"].iloc[2][0] == "A"  # Was 'A', stays 'A'
    assert result["sequence"].iloc[2][2] == "G"  # Was 'G', stays 'G'
    assert result["sequence"].iloc[3][0] == "A"  # Was 'A', stays 'A'
    assert result["sequence"].iloc[3][2] == "G"  # Was '-', becomes 'G'
