# Clustering an MSA

Clustering splits one MSA into subsets of related sequences. This is the central
trick behind AF-Cluster: a folding model given a single cluster often predicts a
different conformation than the same model given the full MSA, which is how
alternative states get sampled.

Clusterers **add a column** rather than returning separate frames:

| Tool | Column added | Needs |
|---|---|---|
| AFCluster (DBSCAN) | `cluster_id` | nothing extra |
| KMeans | `cluster_id` | ESM3 only for `encoding="esm"` |
| Ward centroid merge | `ward_id` | an existing `cluster_id` |

So the workflow is always: cluster, inspect, then save the clusters you want as
separate MSAs.

## AFCluster (DBSCAN)

Follows Wayment-Steele et al. (2024).

```python
from frankenmsa.cluster import AFCluster

clustered = AFCluster().cluster(
    msa,
    eps=0.5,                   # neighbourhood radius
    min_samples=5,             # smallest acceptable cluster
    columns=None,              # extra numeric columns to include
    consensus_sequence=False,  # add a per-cluster consensus column
    levenshtein=False,         # add distances to query and consensus
    verbose=False,
)
```

**`eps` is the parameter that matters.** DBSCAN groups sequences that are within
`eps` of each other; everything too far from any dense group is labelled
**`cluster_id == -1`, the noise cluster**. Too small and almost everything lands
in `-1`; too large and everything collapses into one cluster. A first run that
produces one giant cluster or nothing but noise is an `eps` problem, not a
`min_samples` problem.

Rather than guessing, sweep it:

```python
clusterer = AFCluster()
best_eps = clusterer.gridsearch_eps(
    msa,
    desired_clusters="max",   # or an integer to aim for a specific count
    min_eps=3, max_eps=20, step=0.5,
    data_frac=0.25,           # subsample for speed
    min_samples=3,
)
clustered = clusterer.cluster(msa, eps=best_eps, min_samples=5)
```

The class remembers the searched value, so `cluster(msa, eps=None)` after a
search reuses it. Note the mismatch to watch for: the GUI's epsilon box defaults
to `0.5` while its range slider spans 3-20 (the `gridsearch_eps` defaults). The
right scale depends on the sequences, which is exactly why the sweep is worth
running once per new MSA.

`consensus_sequence=True` and `levenshtein=True` add useful columns
(`consensus_sequence`, `levenshtein_query`, `levenshtein_consensus`) for judging
how far a cluster sits from the query, at some cost. The GUI leaves both off.

## KMeans

```python
from frankenmsa.cluster import KMeans

clustered = KMeans().cluster(
    msa,
    n_clusters=5,
    encoding="onehot",   # "onehot" | "esm" | "numvector"
    columns=None,
)
```

Unlike DBSCAN, KMeans always produces exactly `n_clusters` groups and has no
noise cluster — every sequence is assigned somewhere, including outliers. Use it
when the user wants a fixed number of subsets; use AFCluster when they want
whatever natural groups exist.

**Encodings:**

- `"onehot"` — one-hot over the aligned characters. Needs nothing extra and
  groups by column-wise identity, so it is sensitive to alignment quality.
- `"esm"` — mean-pooled ESM3 (`esmc_300m`) embeddings. Groups by learned
  similarity, which catches remote relatives that look dissimilar column by
  column. Similar in spirit to VC-MSA. **Needs ESM3 installed** (see
  `install.md`); check `importlib.util.find_spec("esm")` first. The model is
  cached between calls, but embedding thousands of sequences on CPU is slow —
  warn before starting a large run.
- `"numvector"` — numeric vector encoding; cheaper than ESM, coarser than
  one-hot.

Extra `columns` must be numeric; `sequence` is the only non-numeric column the
clusterers accept.

## Ward centroid merge

A **second pass**, not a clusterer. It merges existing AFCluster groups
hierarchically using size-weighted Ward linkage over the cluster centroids, so a
run that produced 40 small clusters can be reduced to a handful of meaningful
ones. See Piomponi et al. (2025) for the application to AF conformational
ensembles.

```python
from frankenmsa.cluster.workflows import run_ward_centroid_merge

merged = run_ward_centroid_merge(clustered, n_clusters=3, encoding=None)
```

It requires `cluster_id` to exist and **returns `None` if it does not** — so
always run AFCluster first and check the result before using it. The output adds
`ward_id` while keeping `cluster_id`, so both groupings stay available.

This merges centroids of existing groups; it is not a fresh Ward clustering over
every sequence.

## Saving clusters as MSAs

```python
from frankenmsa.cluster.workflows import save_cluster_subsets

msa_data = save_cluster_subsets(
    msa_data,
    main_msa="my_msa",
    cluster_column="cluster_id",            # or "ward_id" after a Ward merge
    selected=[0, 1, 2],                     # or ["all"] for every cluster
    name_template="{main}_cluster_{cluster}",
)
```

`selected=["all"]` expands to every cluster id present. The GUI uses three
different name templates so the three methods do not overwrite each other:
`{main}_selected_cluster_{cluster}` for AFCluster,
`{main}_ward_cluster_{cluster}` for Ward, and the KMeans save uses its own.
Pick a template that encodes the method when saving more than one.

To write clusters straight to disk instead of the store, the AFCluster object
has `write_a3m(directory, prefix="cluster_")` and `write_cluster_table(...)`.

## Inspecting the result

```python
from frankenmsa.cluster.workflows import cluster_pca_projection, cluster_dropdown_options, numeric_column_options

rest, query = cluster_pca_projection(clustered, encoding=None)   # 2D PCA for plotting
options = cluster_dropdown_options(clustered, cluster_column="cluster_id")
```

`cluster_pca_projection` returns the projected sequences and the query point
separately, which is what the GUI plots. `AFCluster` also carries its own
`pca(...)` and `tsne(...)` plotting helpers for a quick matplotlib look.

Before saving, it is worth reporting the cluster sizes — a clustering where one
cluster holds 95% of the sequences is technically a success and practically
useless:

```python
print(clustered["cluster_id"].value_counts())
```

## Typical end-to-end

```python
from frankenmsa.utils import read_a3m, write_a3m
from frankenmsa.cluster import AFCluster
from frankenmsa.cluster.workflows import save_cluster_subsets

msa = read_a3m("input.a3m")

clusterer = AFCluster()
eps = clusterer.gridsearch_eps(msa, desired_clusters="max")
clustered = clusterer.cluster(msa, eps=eps, min_samples=5)

sizes = clustered["cluster_id"].value_counts()
print(f"eps={eps}, {len(sizes)} clusters, {sizes.get(-1, 0)} noise sequences")

store = save_cluster_subsets(
    {"input": clustered.to_dict("list")}, "input",
    selected=["all"], name_template="{main}_cluster_{cluster}",
)
```

Note that CSV is the format that preserves `cluster_id` and `ward_id`; A3M drops
every column except header and sequence. Export to CSV when the clustering
itself needs to survive, and to A3M when the subsets are going to a folding
model.
