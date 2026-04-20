import pandas as pd
import pytest

from frankenmsa.utils.msatools import build_combined_msa_name
from frankenmsa.utils.msatools import combine_msa_operations
from frankenmsa.utils.msatools import slice_rows


def make_msa(*sequences: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "header": [f"seq{i}" for i in range(len(sequences))],
            "sequence": list(sequences),
        }
    )


def test_slice_rows_returns_requested_window():
    df = make_msa("AAAA", "BBBB", "CCCC", "DDDD")

    result = slice_rows(df, 1, 3)

    assert result["sequence"].tolist() == ["BBBB", "CCCC"]


def test_build_combined_msa_name_uses_requested_name_or_next_default():
    msa_data = {"combined_1": {}, "combined_2": {}, "other": {}}

    assert build_combined_msa_name(msa_data) == "combined_3"
    assert build_combined_msa_name(msa_data, " custom ") == "custom"


def test_combine_msa_operations_concatenates_horizontally_with_slices():
    left = make_msa("AAAA", "BBBB")
    right = make_msa("CCCC", "DDDD")

    result = combine_msa_operations(
        [left, right],
        ["horizontal", "horizontal"],
        horizontal_ranges=[(0, 2), (1, 3)],
        vertical_ranges=[(0, 2), (0, 2)],
    )

    assert result["sequence"].tolist() == ["AACC", "BBDD"]


def test_combine_msa_operations_adjusts_depth_for_horizontal_merge():
    left = make_msa("AAAA", "BBBB", "CCCC")
    right = make_msa("XX", "YY")

    result = combine_msa_operations(
        [left, right],
        ["horizontal", "horizontal"],
        horizontal_ranges=[(0, 4), (0, 2)],
        vertical_ranges=[(0, 3), (0, 2)],
    )

    assert result["sequence"].tolist() == ["AAAAXX", "BBBBYY", "CCCCXX"]


def test_combine_msa_operations_stacks_vertically_with_length_normalization():
    top = make_msa("AAAA", "BBBB")
    bottom = make_msa("CC", "DD")

    result = combine_msa_operations(
        [top, bottom],
        ["horizontal", "vertical"],
        horizontal_ranges=[(0, 4), (0, 2)],
        vertical_ranges=[(0, 2), (0, 2)],
    )

    assert result["sequence"].tolist() == ["AAAA", "BBBB", "CC--", "DD--"]


def test_combine_msa_operations_requires_matching_metadata_lengths():
    msa = make_msa("AAAA")

    with pytest.raises(ValueError, match="directions"):
        combine_msa_operations([msa], [])
