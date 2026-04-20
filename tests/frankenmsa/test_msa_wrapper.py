from __future__ import annotations

import pandas as pd

from frankenmsa.msa import MSA


def make_msa_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "header": ["query", "hit1", "hit2"],
            "sequence": ["Ac-D", "A--D", "ATGD"],
        }
    )


def test_msa_init_and_copy_do_not_share_dataframe():
    df = make_msa_df()
    msa = MSA(df)
    clone = msa.copy()

    clone.uppercase_sequences()

    assert msa.df["sequence"].tolist() == ["Ac-D", "A--D", "ATGD"]
    assert clone.df["sequence"].tolist() == ["AC-D", "A--D", "ATGD"]


def test_msa_init_wraps_dataframe_without_copying():
    df = make_msa_df()
    msa = MSA(df)

    assert msa.df is df


def test_to_dataframe_defaults_to_wrapped_dataframe():
    msa = MSA(make_msa_df())

    assert msa.to_dataframe() is msa.df
    assert msa.to_dataframe(copy=True) is not msa.df


def test_getitem_column_slice_returns_new_msa_without_mutating_original():
    msa = MSA(make_msa_df())

    sliced = msa[1:3]

    assert isinstance(sliced, MSA)
    assert sliced.df["sequence"].tolist() == ["c-", "--", "TG"]
    assert msa.df["sequence"].tolist() == ["Ac-D", "A--D", "ATGD"]


def test_getitem_uses_column_then_row_order():
    msa = MSA(
        pd.DataFrame(
            {
                "header": ["q", "a", "b", "c"],
                "sequence": ["ABCDEFG", "HIJKLMN", "OPQRSTU", "VWXYZ--"],
            }
        )
    )

    sliced = msa[1:4, 1:3]

    assert sliced.df["header"].tolist() == ["a", "b"]
    assert sliced.df["sequence"].tolist() == ["IJK", "PQR"]


def test_getitem_integer_row_and_column_selectors_return_single_residue_msa():
    msa = MSA(make_msa_df())

    sliced = msa[2, 1]

    assert isinstance(sliced, MSA)
    assert sliced.depth == 1
    assert sliced.df["header"].tolist() == ["hit1"]
    assert sliced.df["sequence"].tolist() == ["-"]


def test_getitem_rejects_more_than_two_selectors():
    msa = MSA(make_msa_df())

    try:
        _ = msa[1:3, 0:2, 0:1]
    except IndexError as error:
        assert "at most two selectors" in str(error)
    else:
        raise AssertionError("Expected IndexError for too many selectors")


def test_from_a3m_and_to_a3m_string_round_trip(tmp_path):
    path = tmp_path / "sample.a3m"
    path.write_text(">query\nAC-D\n>hit1\nA--D\n")

    msa = MSA.from_a3m(path)

    assert msa.depth == 2
    assert ">query" in msa.to_a3m_string()


def test_uppercase_sequences_forwards_and_mutates_in_place(monkeypatch):
    called = {"count": 0}

    def fake_uppercase(df):
        called["count"] += 1
        result = df.copy()
        result["sequence"] = result["sequence"].str.upper()
        return result

    monkeypatch.setattr("frankenmsa.msa.msatools.uppercase_sequences", fake_uppercase)

    msa = MSA(make_msa_df())
    returned = msa.uppercase_sequences()

    assert returned is msa
    assert called["count"] == 1
    assert msa.df["sequence"].tolist() == ["AC-D", "A--D", "ATGD"]


def test_dataframe_methods_receive_wrapped_dataframe_without_copy(monkeypatch):
    observed = {}

    def fake_lowercase(df):
        observed["same_object"] = df is msa.df
        df["sequence"] = df["sequence"].str.lower()
        return df

    monkeypatch.setattr("frankenmsa.msa.msatools.lowercase_sequences", fake_lowercase)

    msa = MSA(make_msa_df())
    msa.lowercase_sequences()

    assert observed["same_object"] is True
    assert msa.df["sequence"].tolist() == ["ac-d", "a--d", "atgd"]


def test_combine_returns_new_msa(monkeypatch):
    left = MSA(pd.DataFrame({"header": ["q"], "sequence": ["AAAA"]}))
    right = MSA(pd.DataFrame({"header": ["q"], "sequence": ["CCCC"]}))

    def fake_combine(msas, directions, horizontal_ranges=None, vertical_ranges=None):
        assert msas[0] is left.df
        assert msas[1] is right.df
        assert len(msas) == 2
        assert directions == ["horizontal", "horizontal"]
        return pd.DataFrame({"header": ["q"], "sequence": ["AAAACCCC"]})

    monkeypatch.setattr("frankenmsa.msa.msatools.combine_msa_operations", fake_combine)

    combined = MSA.combine([left, right], ["horizontal", "horizontal"])

    assert isinstance(combined, MSA)
    assert combined.df["sequence"].tolist() == ["AAAACCCC"]


def test_concat_horizontal_returns_new_msa_without_mutating_inputs():
    left = MSA(pd.DataFrame({"header": ["q", "h1"], "sequence": ["AAAA", "BBBB"]}))
    right = MSA(pd.DataFrame({"header": ["q", "h2"], "sequence": ["CCCC", "DDDD"]}))

    combined = left.concat_horizontal(right)

    assert isinstance(combined, MSA)
    assert combined.df["sequence"].tolist() == ["AAAACCCC", "BBBBDDDD"]
    assert left.df["sequence"].tolist() == ["AAAA", "BBBB"]
    assert right.df["sequence"].tolist() == ["CCCC", "DDDD"]


def test_concat_vertical_returns_new_msa_without_mutating_inputs():
    top = MSA(pd.DataFrame({"header": ["q", "h1"], "sequence": ["AAAA", "BBBB"]}))
    bottom = MSA(pd.DataFrame({"header": ["q2", "h2"], "sequence": ["CC", "DD"]}))

    combined = top.concat_vertical(bottom)

    assert isinstance(combined, MSA)
    assert combined.df["sequence"].tolist() == ["AAAA", "BBBB", "CC--", "DD--"]
    assert top.df["sequence"].tolist() == ["AAAA", "BBBB"]
    assert bottom.df["sequence"].tolist() == ["CC", "DD"]


def test_add_operator_uses_horizontal_concat():
    left = MSA(pd.DataFrame({"header": ["q"], "sequence": ["AAAA"]}))
    right = MSA(pd.DataFrame({"header": ["q"], "sequence": ["CCCC"]}))

    combined = left + right

    assert isinstance(combined, MSA)
    assert combined.df["sequence"].tolist() == ["AAAACCCC"]


def test_truediv_operator_uses_vertical_concat():
    top = MSA(pd.DataFrame({"header": ["q"], "sequence": ["AAAA"]}))
    bottom = MSA(pd.DataFrame({"header": ["q2"], "sequence": ["CC"]}))

    combined = top / bottom

    assert isinstance(combined, MSA)
    assert combined.df["sequence"].tolist() == ["AAAA", "CC--"]


def test_concat_rejects_unsupported_input_type():
    msa = MSA(pd.DataFrame({"header": ["q"], "sequence": ["AAAA"]}))

    try:
        _ = msa.concat_horizontal("not-an-msa")
    except TypeError as error:
        assert "another MSA or pandas DataFrame" in str(error)
    else:
        raise AssertionError("Expected TypeError for unsupported concat input")


def test_split_chains_wraps_dataframes_as_msa_objects(monkeypatch):
    chain_a = pd.DataFrame({"header": ["qA"], "sequence": ["AAAA"]})
    chain_b = pd.DataFrame({"header": ["qB"], "sequence": ["BBBB"]})

    monkeypatch.setattr(
        "frankenmsa.msa.msatools.split_chains",
        lambda df: [chain_a, chain_b],
    )

    result = MSA(make_msa_df()).split_chains()

    assert len(result) == 2
    assert all(isinstance(item, MSA) for item in result)
    assert result[0].df["sequence"].tolist() == ["AAAA"]
    assert result[1].df["sequence"].tolist() == ["BBBB"]


def test_cluster_afcluster_mutates_wrapper_dataframe(monkeypatch):
    def fake_cluster(self, sequences, **kwargs):
        result = sequences.copy()
        result["cluster_id"] = [0, 1, 1]
        return result

    monkeypatch.setattr("frankenmsa.msa.af_cluster.AFCluster.cluster", fake_cluster)

    msa = MSA(make_msa_df()).cluster_afcluster(eps=0.5, min_samples=2)

    assert "cluster_id" in msa.df.columns
    assert msa.df["cluster_id"].tolist() == [0, 1, 1]


def test_gap_counts_returns_series_without_mutating_dataframe(monkeypatch):
    called = {"count": 0}

    def fake_gap_counts(df, normalize_length="max"):
        called["count"] += 1
        return pd.Series([0, 1, 2], name="gap_count")

    monkeypatch.setattr("frankenmsa.msa.summaries.gap_counts", fake_gap_counts)

    msa = MSA(make_msa_df())
    result = msa.gap_counts()

    assert called["count"] == 1
    assert result.tolist() == [0, 1, 2]
    assert "cluster_id" not in msa.df.columns


def test_visualize_forwards_to_visual_module(monkeypatch):
    sentinel = object()

    monkeypatch.setattr(
        "frankenmsa.msa.alignment_chart.visualize_msa",
        lambda df, backend="matplotlib": sentinel,
    )

    msa = MSA(make_msa_df())

    assert msa.visualize(backend="plotly") is sentinel
