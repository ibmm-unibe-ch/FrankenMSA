import numpy as np
from sklearn.cluster import AgglomerativeClustering
from ..utils.seqtools import get_encoding_func

def ward_linking(df, n_clusters, encoding):
    if "cluster_id" not in df.columns:
        return None

    seq_len = len(df.iloc[0]["sequence"]) if len(df) else 0
    if seq_len == 0:
        return None
    centroids = []
    cluster_keys = []
    enconding_func = get_encoding_func(encoding)
    for cid, sub in df.groupby("cluster_id"):
        X = enconding_func(sub["sequence"].values, max_len=seq_len)
        centroids.append(X.mean(axis=0))
        cluster_keys.append(cid)
    centroids = np.vstack(centroids)

    model = AgglomerativeClustering(n_clusters=int(n_clusters), linkage="ward")
    ward_labels = model.fit_predict(centroids)

    cid_to_wid = {cid: int(w) for cid, w in zip(cluster_keys, ward_labels)}
    df["ward_id"] = df["cluster_id"].map(cid_to_wid)
    return df.to_dict("list")
   