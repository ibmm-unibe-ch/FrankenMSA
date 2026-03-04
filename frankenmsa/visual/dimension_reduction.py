from sklearn.decomposition import PCA
import pandas as pd
from ..utils.seqtools import get_encoding_func 


def compute_PCA(msa:pd.DataFrame, encoding=None):
    df = msa.copy()

    # separate query row (first row) if present
    query = df.iloc[:1]
    rest = df.iloc[1:]

    seq_len = (
        len(query["sequence"].values[0])
        if len(query)
        else len(rest.iloc[0]["sequence"]) if len(rest) else 0
    )
    if seq_len == 0:
        return None, None

    encoding_func = get_encoding_func(encoding)
    rest_onehot = encoding_func(rest["sequence"].values, max_len=seq_len)

    pca = PCA(n_components=2, random_state=42)
    embedding = pca.fit_transform(rest_onehot)
    rest = rest.assign(**{"PC 1": embedding[:, 0], "PC 2": embedding[:, 1]})

    # project query point with the same PCA
    if len(query):
        q_onehot = encoding_func(query["sequence"].values, max_len=seq_len)
        q_embed = pca.transform(q_onehot)
        query = query.assign(**{"PC 1": q_embed[:, 0], "PC 2": q_embed[:, 1]})
    return rest, query