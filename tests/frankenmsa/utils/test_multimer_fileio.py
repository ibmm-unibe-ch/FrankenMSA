import pandas as pd
import pytest

from frankenmsa.utils.fileio import build_multimer_csv, split_dataframe_by_chain
from frankenmsa.utils.multimer_a3m import (
    chain_label,
    is_multimer_a3m_text,
    split_multimer_a3m_file,
)


def test_chain_label_supports_single_and_double_letters():
    assert chain_label(0) == "A"
    assert chain_label(25) == "Z"
    assert chain_label(26) == "AA"
    assert chain_label(27) == "AB"


def test_is_multimer_a3m_text_detects_colabfold_header():
    assert is_multimer_a3m_text("#4,3\t1,1\n>101\nAAAABBB\n")
    assert not is_multimer_a3m_text(">query\nAAAA\n")


def test_split_multimer_a3m_file_returns_per_chain_dataframes(tmp_path):
    a3m_path = tmp_path / "complex.a3m"
    a3m_path.write_text(
        "#4,3\t1,1\n"
        ">101\n"
        "AAAABBB\n"
        ">query\n"
        "AAAA---\n"
        ">hit1\n"
        "A-AA---\n"
        ">query\n"
        "----BBB\n"
        ">hit1\n"
        "----B-B\n",
        encoding="utf-8",
    )

    result = split_multimer_a3m_file(str(a3m_path), "complex")

    assert list(result.keys()) == ["complexA", "complexB"]
    assert result["complexA"].to_dict("list") == {
        "header": ["query", "hit1"],
        "sequence": ["AAAA", "AAA"],
    }
    assert result["complexB"].to_dict("list") == {
        "header": ["query", "hit1"],
        "sequence": ["BBB", "BB"],
    }


def test_split_dataframe_by_chain_splits_and_drops_chain_column():
    df = pd.DataFrame(
        {
            "header": ["q1", "q2", "q1", "q2"],
            "sequence": ["AAAA", "AAAT", "BBBB", "BBBT"],
            "chain": ["A", "A", "B", "B"],
        }
    )

    result = split_dataframe_by_chain(df, "complex")

    assert list(result.keys()) == ["complexA", "complexB"]
    assert "chain" not in result["complexA"].columns
    assert result["complexB"]["sequence"].tolist() == ["BBBB", "BBBT"]


def test_split_dataframe_by_chain_requires_chain_column():
    df = pd.DataFrame({"header": ["q1"], "sequence": ["AAAA"]})

    with pytest.raises(ValueError, match="chain"):
        split_dataframe_by_chain(df, "complex")


def test_build_multimer_csv_adds_chain_labels_in_order():
    msa_data = {
        "msa1": {"header": ["q1", "h1"], "sequence": ["AAAA", "AAAT"]},
        "msa2": {"header": ["q2"], "sequence": ["BBBB"]},
    }

    result = build_multimer_csv(msa_data, ["msa1", "msa2", "msa1"])

    assert result["chain"].tolist() == ["A", "A", "B", "C", "C"]
    assert result["header"].tolist() == ["q1", "h1", "q2", "q1", "h1"]