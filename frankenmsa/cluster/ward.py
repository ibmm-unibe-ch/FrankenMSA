import numpy as np

from ..utils.seqtools import get_encoding_func


def _cluster_centroid_features(df, encoding):
    seq_len = len(df.iloc[0]["sequence"]) if len(df) else 0
    if seq_len == 0:
        return None, None, None

    encoding_func = get_encoding_func(encoding)
    centroids = []
    cluster_keys = []
    cluster_sizes = []

    for cluster_id, sub in df.groupby("cluster_id"):
        encoded = encoding_func(sub["sequence"].values, max_length=seq_len)
        centroids.append(encoded.mean(axis=0).reshape(-1))
        cluster_keys.append(cluster_id)
        cluster_sizes.append(len(sub))

    if not centroids:
        return None, None, None

    return np.vstack(centroids), cluster_keys, np.asarray(cluster_sizes, dtype=float)


def _ward_merge_cost(left, right):
    diff = left["centroid"] - right["centroid"]
    return (
        (left["size"] * right["size"])
        / (left["size"] + right["size"])
        * float(np.dot(diff, diff))
    )


def _weighted_ward_labels(centroids, sizes, n_clusters):
    if n_clusters < 1:
        raise ValueError("n_clusters must be at least 1")
    if len(centroids) < n_clusters:
        raise ValueError(
            f"Cannot merge {len(centroids)} centroid clusters into {n_clusters} clusters"
        )

    active = {
        index: {
            "members": [index],
            "centroid": centroids[index].astype(float, copy=True),
            "size": float(sizes[index]),
        }
        for index in range(len(centroids))
    }
    next_cluster_id = len(centroids)

    while len(active) > n_clusters:
        active_ids = list(active.keys())
        best_pair = None
        best_cost = None
        for left_offset, left_id in enumerate(active_ids[:-1]):
            for right_id in active_ids[left_offset + 1 :]:
                cost = _ward_merge_cost(active[left_id], active[right_id])
                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    best_pair = (left_id, right_id)

        left_id, right_id = best_pair
        left = active.pop(left_id)
        right = active.pop(right_id)
        merged_size = left["size"] + right["size"]
        merged_centroid = (
            left["size"] * left["centroid"] + right["size"] * right["centroid"]
        ) / merged_size
        active[next_cluster_id] = {
            "members": left["members"] + right["members"],
            "centroid": merged_centroid,
            "size": merged_size,
        }
        next_cluster_id += 1

    labels = np.empty(len(centroids), dtype=int)
    final_clusters = sorted(
        active.values(), key=lambda cluster: min(cluster["members"])
    )
    for ward_id, cluster in enumerate(final_clusters):
        labels[cluster["members"]] = ward_id
    return labels


def ward_merge_cluster_centroids(df, n_clusters, encoding=None):
    if "cluster_id" not in df.columns:
        return None

    centroids, cluster_keys, cluster_sizes = _cluster_centroid_features(df, encoding)
    if centroids is None:
        return None

    ward_labels = _weighted_ward_labels(centroids, cluster_sizes, int(n_clusters))
    cluster_to_ward = {
        cluster_id: int(label) for cluster_id, label in zip(cluster_keys, ward_labels)
    }

    df = df.copy()
    df["ward_id"] = df["cluster_id"].map(cluster_to_ward)
    return df


def ward_linking(df, n_clusters, encoding=None):
    return ward_merge_cluster_centroids(df, n_clusters=n_clusters, encoding=encoding)
