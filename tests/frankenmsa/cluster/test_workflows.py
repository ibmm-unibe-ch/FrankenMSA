import pandas as pd

from frankenmsa.cluster import cluster_dropdown_options
from frankenmsa.cluster import numeric_column_options
from frankenmsa.cluster import run_ward_centroid_merge
from frankenmsa.cluster import run_ward_clustering
from frankenmsa.cluster import save_cluster_subsets


def test_numeric_column_options_only_returns_numeric_columns():
    df = pd.DataFrame(
        {
            "header": ["q", "h"],
            "sequence": ["AAAA", "AAAT"],
            "score": [1.0, 2.0],
            "cluster_id": [0, 1],
        }
    )

    assert numeric_column_options(df) == [
        {"label": "score", "value": "score"},
        {"label": "cluster_id", "value": "cluster_id"},
    ]


def test_cluster_dropdown_options_include_all_choice():
    df = pd.DataFrame({"cluster_id": [0, 1, 1]})

    assert cluster_dropdown_options(df, cluster_column="cluster_id", label_prefix="Cluster") == [
        {"label": "All", "value": "all"},
        {"label": "Cluster 0", "value": 0},
        {"label": "Cluster 1", "value": 1},
    ]


def test_save_cluster_subsets_respects_selected_ids():
    msa_data = {
        "main": {
            "header": ["q", "h1", "h2"],
            "sequence": ["AAAA", "AAAT", "BBBB"],
            "cluster_id": [0, 0, 1],
        }
    }

    saved = save_cluster_subsets(
        msa_data,
        "main",
        cluster_column="cluster_id",
        selected=[1],
        name_template="{main}_subset_{cluster}",
    )

    assert "main_subset_1" in saved
    assert saved["main_subset_1"]["sequence"] == ["BBBB"]
    assert "main_subset_0" not in saved


def test_run_ward_clustering_adds_ward_ids():
    df = pd.DataFrame(
        {
            "header": ["q", "h1", "h2", "h3"],
            "sequence": ["AAAA", "AAAT", "CCCC", "CCCT"],
            "cluster_id": [0, 0, 1, 1],
        }
    )

    linked = run_ward_clustering(df, n_clusters=2, encoding="onehot")

    assert isinstance(linked, pd.DataFrame)
    assert "ward_id" in linked.columns
    assert set(linked["ward_id"].unique()) <= {0, 1}


def test_run_ward_centroid_merge_weights_clusters_by_size():
    df = pd.DataFrame(
        {
            "header": ["h0", "h1", "h2", "h3", "h4", "h5"],
            "sequence": ["AAAA", "AAAT", "AAAG", "AAAC", "CCCC", "GGGG"],
            "cluster_id": [0, 0, 0, 0, 1, 2],
        }
    )

    linked = run_ward_centroid_merge(df, n_clusters=2, encoding="numvector")

    ward_ids = linked.groupby("cluster_id")["ward_id"].first().to_dict()
    assert ward_ids[0] == ward_ids[1]
    assert ward_ids[2] != ward_ids[0]


def test_run_ward_centroid_merge_alias_matches_old_name():
    df = pd.DataFrame(
        {
            "header": ["q", "h1", "h2", "h3"],
            "sequence": ["AAAA", "AAAT", "CCCC", "CCCT"],
            "cluster_id": [0, 0, 1, 1],
        }
    )

    renamed = run_ward_centroid_merge(df, n_clusters=2, encoding="numvector")
    legacy = run_ward_clustering(df, n_clusters=2, encoding="numvector")

    pd.testing.assert_frame_equal(renamed, legacy)