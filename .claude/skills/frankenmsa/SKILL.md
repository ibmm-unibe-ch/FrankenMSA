---
name: frankenmsa
description: Run FrankenMSA tasks from the command line or a Python script - building MSAs with MMseqs2 or PLM-Search, inverse folding structures with ProteinMPNN, augmenting orphan sequences with GhostFold, clustering with AFCluster/KMeans/Ward, and editing alignments (filtering, sorting, shuffling, slicing, depth, insertions). Use this skill whenever the user mentions MSAs, multiple sequence alignments, a3m files, inverse folding, ProteinMPNN, GhostFold, AFCluster, PLM-Search, HHfilter, ESM3 embeddings, or asks to install FrankenMSA or its plugins - and also for vaguer alignment work like "my MSA is too shallow", "subsample these sequences" or "remove the gappy ones", even when FrankenMSA is never named.
---

# FrankenMSA

FrankenMSA builds and manipulates multiple sequence alignments (MSAs) for
protein structure prediction. The research premise is that the MSA you feed a
folding model determines what it predicts, so deliberately reshaping the MSA —
clustering it, filtering it, shuffling columns, replacing it with inverse-folded
or synthetic sequences — steers the prediction.

The Python library is the real interface. The Dash app in `app/` is a thin GUI
whose callbacks call the same functions, so prefer the library: it is
scriptable, and anything the GUI can do is reachable from Python.

## The data model

**An MSA is a `pandas.DataFrame` with a `header` and a `sequence` column.**
Tools add columns (`cluster_id`, `ward_id`, `consensus_sequence`). Everything
composes because every tool takes and returns that one shape.

**The first row is the query sequence.** Sorting, shuffling and position-editing
functions treat it specially and keep it pinned by default.

```python
from frankenmsa.utils import read_a3m, write_a3m
msa = read_a3m("input.a3m")      # also read_fasta, decode_a3m for in-memory text
write_a3m(msa, "output.a3m")
```

A3M and FASTA keep only header and sequence. **CSV is the only format that
preserves added columns**, so export clustering results to CSV and send A3M to
folding models. `references/download.md` covers the readers and writers,
including multimer files.

## Which reference to read

Read the one that matches the task. Each is self-contained.

| Task | Reference |
|---|---|
| Installing the package or a plugin; checking what is available | `references/install.md` |
| Building an MSA from a sequence (MMseqs2, PLM-Search) | `references/align.md` |
| Sequences from a structure (ProteinMPNN) | `references/inverse-fold.md` |
| A pseudo-MSA for an orphan sequence (GhostFold) | `references/augment.md` |
| Splitting an MSA into clusters (AFCluster, KMeans, Ward) | `references/cluster.md` |
| Filtering, sorting, shuffling, slicing, depth, editing residues, combining | `references/edit.md` |
| Reading and writing files; **building a multimer MSA** | `references/download.md` |

## Check plugin availability before running

Three capabilities need a separately installed dependency: **inverse folding**
(ProteinMPNN), **GhostFold augmentation**, and **KMeans with
`encoding="esm"`** (ESM3). HHfilter needs hh-suite binaries. Without them the
run fails with a long traceback, so check first and offer the install command
instead of attempting the run — these downloads are large enough that the user
should decide.

```python
from frankenmsa.inverse_fold.protein_mpnn_support import resolve_proteinmpnn_root
from frankenmsa.augment.ghostfold import resolve_ghostfold_command
from frankenmsa.filter.hhsuite import has_hhsuite
import importlib.util

try:
    resolve_proteinmpnn_root()          # RuntimeError if absent
except RuntimeError:
    ...  # python scripts/installers/install_proteinmpnn.py --root ... --install-python-deps

try:
    resolve_ghostfold_command()         # FileNotFoundError if absent
except FileNotFoundError:
    ...  # python scripts/installers/install_ghostfold.py

importlib.util.find_spec("esm")         # None if ESM3 is absent
has_hhsuite()                           # bool
```

Both resolvers honour environment variables first, so a user with an existing
checkout can point at it instead of reinstalling. See `references/install.md`.

## How the pieces fit together

A typical session is: **get an MSA** (align, inverse fold, augment, or load a
file) → **reshape it** (filter, cluster, slice) → **write it out** for a folding
model.

```python
from frankenmsa.utils import read_a3m, write_a3m
from frankenmsa.utils.msatools import filter_gaps, drop_duplicates
from frankenmsa.cluster import AFCluster
from frankenmsa.cluster.workflows import save_cluster_subsets

msa = read_a3m("input.a3m")
msa = drop_duplicates(msa)
msa = filter_gaps(msa, allowed_gaps_faction=0.5)     # fraction, not percent

clusterer = AFCluster()
eps = clusterer.gridsearch_eps(msa, desired_clusters="max")
clustered = clusterer.cluster(msa, eps=eps, min_samples=5)
print(clustered["cluster_id"].value_counts())        # -1 is the noise cluster

store = save_cluster_subsets(
    {"msa": clustered.to_dict("list")}, "msa",
    selected=["all"], name_template="{main}_cluster_{cluster}",
)
for name, data in store.items():
    import pandas as pd
    write_a3m(pd.DataFrame(data), f"{name}.a3m")
```

## Multimers

A multimer MSA describes a complex of several chains. Which route to take
depends on whether the chains need to be *paired* — matched row by row across
chains, usually by species:

- **Paired**: one MMseqs2 query with the chains joined by `:` and a pairing mode
  of `"greedy"` or `"complete"`. Co-evolutionary signal between the chains
  survives, which is what AlphaFold-Multimer benefits from. See `align.md`.
- **Unpaired**: align each chain separately, then stack the per-chain MSAs with
  `combine_unpaired_a3m` (or `build_multimer_csv`). Simpler, and the only option
  when the chains were searched independently. See `download.md`.
- **Fused into one chain**: horizontal concatenation on the Combine page makes a
  single longer sequence — a chimera, not a complex. See `edit.md`.

```python
from frankenmsa.utils import write_a3m
from frankenmsa.utils.fileio import combine_unpaired_a3m

write_a3m(chain_a, "A.a3m"); write_a3m(chain_b, "B.a3m")
combine_unpaired_a3m(["A.a3m", "B.a3m"], "complex.a3m")   # input order = chains A, B, ...
```

Chains may differ in depth — each keeps all of its sequences. One thing to know,
detailed in `download.md`: a combine → split round-trip duplicates the query row
unless you pass `add_anchor=False`.

## Working habits

**Editing overwrites.** The GUI writes every edit back over the current MSA, and
the library functions return a new frame. When scripting an exploration, keep
the original so results stay comparable.

**Report what happened.** Sequence counts before and after a filter, cluster
sizes after clustering, `num_sequences` after inverse folding. A filter that
removed everything and a clustering that produced one cluster both "succeed"
silently, and the count is what reveals it.

**Long-running steps deserve a warning.** ProteinMPNN without a GPU, ESM3
embeddings on CPU, GhostFold, and PLM-Search with a low cutoff and a high
`max_sequences` all take real time. Say so before starting rather than letting
it look hung.

## Still missing from this skill

Not yet covered: the Visualize page (alignment chart, gap/conservation/identity
profiles in `frankenmsa.visual`) and the Colab notebook as an entry point. A
bundled `scripts/` helper for the align → cluster → save pipeline would also
save rewriting the same twenty lines; see the end of `references/cluster.md` for
what that script would contain.
