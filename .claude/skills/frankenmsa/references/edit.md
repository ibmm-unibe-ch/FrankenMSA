# Editing an MSA

Everything the Edit page does, as library calls. All of these live in
`frankenmsa.utils.msatools` unless noted, take a DataFrame with a `sequence`
column, and return a new DataFrame.

**The first row is the query sequence.** Sorting, shuffling and the
position-editing functions treat it specially, usually keeping it pinned at the
top via a `preserve_query` or `include_query` argument. Nothing in the library
enforces it, so if your first row is not the query, these defaults are wrong for
you.

**The GUI overwrites in place.** Every Edit callback writes the result back over
the current MSA (`msa_data[main] = new.to_dict("list")`). Only "Slice MSA copy"
creates a new entry. When scripting, keep the original around if you want to
compare before and after.

## Contents

- [Filter](#filter) — gaps, HHfilter, regex, pandas query, duplicates
- [Sort and shuffle](#sort-and-shuffle) — identity, gaps, column, row shuffle, column shuffle
- [Slice and crop](#slice-and-crop) — slice, depth, unify length
- [Edit sequences](#edit-sequences) — case, gaps, insert, replace, fix to query
- [MSA management](#msa-management) — rename, duplicate, separate query, overview
- [Combining MSAs](#combining-msas)
- [In the library but not in the GUI](#in-the-library-but-not-in-the-gui)

## Filter

### Remove gappy sequences

```python
from frankenmsa.utils.msatools import filter_gaps
filtered = filter_gaps(msa, allowed_gaps_faction=0.5)   # keep sequences <= 50% gaps
```

Takes a **fraction between 0 and 1** and raises `ValueError` outside that range.
The GUI slider is a percentage and divides by 100 before calling, so "50" in the
app is `0.5` here. Note the parameter name is misspelled `allowed_gaps_faction`
in the library — `allowed_gaps_fraction=` raises `TypeError`.

### HHfilter (HH-suite)

```python
from frankenmsa.filter.hhsuite import hhfilter, has_hhsuite

if not has_hhsuite():
    ...  # hh-suite binaries are not on PATH

filtered = hhfilter(
    msa,
    diff=10,                   # -diff:  sequence diversity factor, minimum to retain
    max_pairwise_identity=100, # -id:    drop pairs more identical than this
    min_query_coverage=50,     # -cov:   minimum coverage of the query
    min_query_identity=0,      # -qid:   minimum identity to the query
    min_query_score=-20,       # -qsc:   minimum alignment score to the query
    target_diversity=0,        # -neff:  0 disables
)
```

This shells out to the `hhfilter` binary, so check `has_hhsuite()` first and
point the user at hh-suite (conda: `conda install -c bioconda hhsuite`) if it is
missing. The defaults are the GUI's defaults and are a reasonable starting
point; `diff` is the knob that most directly controls how much survives.

### Regex

```python
from frankenmsa.utils.msatools import filter_by_regex
filtered = filter_by_regex(msa, pattern=r"^M.*K$", method="contains", inverse=False)
```

`method="contains"` matches anywhere in the sequence, `method="match"` anchors at
the start. `inverse=True` keeps the sequences that do *not* match. Remember the
pattern runs against the **aligned** sequence, so gaps and lowercase insertions
are part of the string — `"GG"` will not match `"G-G"`. Uppercase the MSA or
convert insertions to gaps first if that matters.

### Free pandas query

```python
from frankenmsa.utils.msatools import filter_by_query
filtered = filter_by_query(msa, "cluster_id == 2 and levenshtein_query < 30")
```

Passes the string to `DataFrame.query`, so it can use any column, including ones
added by clustering. This is the escape hatch when the other filters do not fit.

### Drop duplicates

```python
from frankenmsa.utils.msatools import drop_duplicates
deduped = drop_duplicates(msa, keep_first=True)
```

Deduplicates on the sequence, not the header, so identical sequences with
different headers collapse into one.

## Sort and shuffle

```python
from frankenmsa.utils.msatools import sort_identity, sort_gaps, sort_by_column, shuffle_rows, shuffle_msa

sort_identity(msa, ascending=False)   # by identity to the query (first row)
sort_gaps(msa, ascending=True)        # by gap count
sort_by_column(msa, "cluster_id", ascending=True, preserve_query=True)
shuffle_rows(msa, random_state=42, preserve_query=True)
```

`preserve_query=True` keeps the first row pinned at the top; the GUI always does
this. For `sort_identity` and `sort_gaps` the GUI exposes ascending/descending
as a radio and defaults to descending.

### Column-wise shuffle

```python
shuffled = shuffle_msa(msa, start=0, end=120, preserve_gaps=True, random_state=42)
```

This is the interesting one for steering folding models: it shuffles residues
*within each column* over the row range `start:end`, destroying co-evolutionary
signal while keeping each column's composition. The query row stays fixed.
`preserve_gaps=True` leaves gap positions where they are and shuffles only the
residues, which keeps the alignment's shape intact. Set `random_state` when the
user needs a reproducible result — the GUI exposes this as "Advanced → Random
seed".

## Slice and crop

### Slice columns (alignment positions)

```python
from frankenmsa.utils.msatools import slice_sequences
sliced = slice_sequences(msa, start=10, end=120)
```

Crops every sequence to positions 10-120. The GUI's "Slice MSA" overwrites the
current MSA; "Slice MSA copy" writes a new one named `{name}_{start}_{end}`,
which is the safer habit when scripting an exploration.

### Slice rows (sequences)

```python
from frankenmsa.utils.msatools import slice_rows
subset = slice_rows(msa, start=0, end=500)
```

### Set depth

```python
from frankenmsa.utils.msatools import adjust_depth
resized = adjust_depth(msa, depth=512)
```

One function for both directions: it crops if the MSA is deeper than `depth` and
duplicates existing entries if it is shallower. Padding by duplication is what
makes it possible to hit a fixed depth a folding model expects, but it adds no
new information — say so if a user seems to expect real sequences.

### Unify sequence length

```python
from frankenmsa.utils.msatools import unify_length
unify_length(msa, "first")   # crop/pad everything to the query's length
unify_length(msa, "max")     # pad everything to the longest sequence
unify_length(msa, "min")     # crop everything to the shortest
unify_length(msa, 250)       # or an explicit integer
```

The GUI offers the first two: "Match Query Length" is `"first"`, "Pad to Longest
Sequence" is `"max"`. Padding uses `-`, cropping truncates from the right.

## Edit sequences

### Whole-MSA character operations

```python
from frankenmsa.utils.msatools import (
    replace_insertions_with_gaps,   # lowercase insertion characters -> '-'
    replace_unknown_with_gaps,      # 'X' -> '-'
    uppercase_sequences,
    lowercase_sequences,
)
```

In A3M, lowercase means an insertion relative to the query. Uppercasing therefore
*changes the meaning* of the alignment rather than just its appearance — use
`replace_insertions_with_gaps` when the goal is a clean aligned block, and
`uppercase_sequences` only when a downstream tool demands uppercase.

### Insert, replace and fix positions

```python
from frankenmsa.utils.msatools import insert_at, replace_at, fix_at

insert_at(msa, sequence="ACGT", index=10, include_query=True)
replace_at(msa, index=10, replacement="ACGT", include_query=False)
fix_at(msa, indices=[0, 5, 10, 11, 12, 13, 14, 15])
```

`insert_at` shifts existing residues right; `replace_at` overwrites in place and
keeps the length. Watch the defaults, which differ and match the GUI's
checkboxes: `insert_at` includes the query by default, `replace_at` does not.
Excluding the query means the query row keeps its original length while the
others grow — usually not what you want from an insert.

`fix_at` copies the query's residues into every other sequence at the given
positions, which is how you force a motif to be conserved across the MSA. The
GUI accepts ranges as text (`"0, 5, 10-15"`); `parse_indices_input` in
`app/pages/edit.py` expands that into the list `fix_at` wants.

## MSA management

**Rename** and **duplicate** are dictionary operations on the store, not library
functions — rename moves the key, duplicate copies the DataFrame under a new
name (`{name}_N` when no name is given).

**Separate query** is also implemented in the page: it moves the first row into
its own single-sequence MSA named `{name}_query` and leaves the rest behind.
Useful when a tool should see the query separately from its homologs.

**Overview** numbers (sequence count, min/max/average length, gap count) are
plain pandas on the `sequence` column. The consensus sequence comes from
`frankenmsa.utils.seqtools.consensus_sequence(df["sequence"])`.

## Combining MSAs

From the Combine page, same module:

```python
from frankenmsa.utils.msatools import combine_msa_operations, build_combined_msa_name

combined = combine_msa_operations(
    msas=[msa_a, msa_b],
    directions=["horizontal", "vertical"],
    horizontal_ranges=[(0, 100), (0, 80)],   # column slice per input
    vertical_ranges=[(0, 500), (0, 500)],    # row slice per input
)
```

`"horizontal"` concatenates sequences side by side (longer sequences, as for a
chimera or a multimer block); `"vertical"` stacks more sequences on top of each
other (a deeper MSA). The ranges are applied per input before combining, so this
single call covers "take the first 100 columns of A and glue the first 80 of B
onto it".

## In the library but not in the GUI

These have no page but are often what a scripted task actually needs:

- `crop_to_depth(df, depth)` / `extend_to_depth(df, depth)` — the two halves of
  `adjust_depth`, when you want only one direction.
- `filter_identity(df, ...)` — filter by identity to the query.
- `remove_at(df, ...)` — delete a slice of positions.
- `split_chains(df)` / `merge_chains(dfs)` — split a multimer block into chains
  and put it back together.
- `head(df, n)` / `tail(df, n)` — quick looks at the top or bottom.
