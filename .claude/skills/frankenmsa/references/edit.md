# Editing an MSA

Every function here lives in `frankenmsa.utils.msatools` unless noted, takes a
DataFrame with a `sequence` column, and returns a new DataFrame. They compose
freely, so a pipeline is just a chain of calls.

**The first row is the query sequence.** Sorting, shuffling and the
position-editing functions treat it specially, usually keeping it pinned at the
top through a `preserve_query` or `include_query` argument. Nothing enforces the
convention, so if your first row is not the query, those defaults are wrong for
you.

## Contents

- [Filtering](#filtering) — gaps, identity, HHfilter, regex, pandas query, duplicates
- [Sorting and shuffling](#sorting-and-shuffling)
- [Slicing, depth and length](#slicing-depth-and-length)
- [Editing residues](#editing-residues)
- [Multimer chains](#multimer-chains)
- [Inspecting](#inspecting)
- [Combining MSAs](#combining-msas)

## Filtering

### Remove gappy sequences

```python
from frankenmsa.utils.msatools import filter_gaps

filtered = filter_gaps(msa, allowed_gaps_faction=0.5)   # keep sequences <= 50% gaps
```

The threshold is a **fraction between 0 and 1**; anything outside that range
raises `ValueError`. The parameter name is misspelled `allowed_gaps_faction` in
the library, so `allowed_gaps_fraction=` raises `TypeError`.

### Filter by identity to the query

```python
from frankenmsa.utils.msatools import filter_identity

close = filter_identity(msa, identity_threshold=0.3, method="keep")
distant = filter_identity(msa, identity_threshold=0.9, method="remove")
```

`identity_threshold` is the fraction of identical residues against the first
row. `method="keep"` retains sequences above the threshold, `"remove"` drops
those below it. Useful for trimming near-duplicates of the query, or for keeping
only close homologs.

### HHfilter (HH-suite)

```python
from frankenmsa.filter.hhsuite import hhfilter, has_hhsuite

if not has_hhsuite():
    ...   # the hh-suite binaries are not on PATH

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
point the user at hh-suite (`conda install -c bioconda hhsuite`) if it is
missing. `diff` is the knob that most directly controls how much survives.

### Reaching an exact depth

`diff` is a **diversity target, not a row cap**. hhfilter keeps adding
sequences until the alignment is diverse enough, so the result routinely
overshoots: on 40 unrelated sequences, `diff=3` returns 39 rows. It can also
undershoot, when the input simply does not hold that many distinct sequences.

When the user asked for a specific depth, correct the result afterwards and say
what happened — silently returning 39 sequences for a request of 3, or 4 for a
request of 6, is the kind of thing that goes unnoticed until much later.

```python
from frankenmsa.filter.hhsuite import hhfilter, has_hhsuite
from frankenmsa.utils.msatools import adjust_depth

def to_depth(msa, depth, label="MSA"):
    """Reach exactly `depth` rows, reporting which route was taken."""
    if has_hhsuite():
        out = hhfilter(msa.copy(), diff=depth)
        route = f"hhfilter(diff={depth})"
    else:
        out, route = msa.copy(), "no hh-suite, trimming/repeating only"

    if len(out) > depth:
        out = out.iloc[:depth].reset_index(drop=True)
        route += f", kept the first {depth}"
    elif len(out) < depth:
        print(f"{label}: only {len(out)} sequences available for a depth of "
              f"{depth}; repeating sequences to fill")
        out = adjust_depth(out, depth)
        route += ", repeated to fill"

    print(f"{label}: {route} -> {len(out)} rows")
    return out
```

`adjust_depth` is the fallback for both directions on its own: it keeps the
first `depth` rows when the MSA is deeper, and repeats from the top when it is
shallower. Repeating adds no new information, which is exactly why it is worth
telling the user it happened.

### Regex

```python
from frankenmsa.utils.msatools import filter_by_regex

filtered = filter_by_regex(msa, pattern=r"^M.*K$", method="contains", inverse=False)
```

`method="contains"` matches anywhere in the sequence, `method="match"` anchors
at the start, and `inverse=True` keeps the sequences that do *not* match.

The pattern runs against the **aligned** sequence, so gaps and lowercase
insertions are part of the string: `"GG"` does not match `"G-G"`. Call
`replace_insertions_with_gaps` or `uppercase_sequences` first when that matters.

### Arbitrary pandas query

```python
from frankenmsa.utils.msatools import filter_by_query

filtered = filter_by_query(msa, "cluster_id == 2 and levenshtein_query < 30")
```

Hands the string to `DataFrame.query`, so any column works, including ones added
by clustering. This is the escape hatch when the other filters do not fit.

### Drop duplicates

```python
from frankenmsa.utils.msatools import drop_duplicates

deduped = drop_duplicates(msa, keep_first=True)
```

Deduplicates on the sequence rather than the header, so identical sequences with
different names collapse into one.

## Sorting and shuffling

```python
from frankenmsa.utils.msatools import (
    sort_identity, sort_gaps, sort_by_column, shuffle_rows, shuffle_msa,
)

sort_identity(msa, ascending=False)    # by identity to the query (first row)
sort_gaps(msa, ascending=True)         # by gap count
sort_by_column(msa, "cluster_id", ascending=True, preserve_query=True)
shuffle_rows(msa, random_state=42, preserve_query=True)
```

`preserve_query=True` keeps the first row pinned at the top. Set `random_state`
on `shuffle_rows` whenever the result has to be reproducible.

### Column-wise shuffle

```python
shuffled = shuffle_msa(msa, start=0, end=120, preserve_gaps=True, random_state=42)
```

This is the interesting one for steering folding models: it shuffles residues
*within each column* across the row range `start:end`, destroying the
co-evolutionary signal while leaving each column's composition intact. The query
row stays fixed. `preserve_gaps=True` shuffles only the residues and leaves gap
positions where they are, so the alignment keeps its shape.

## Slicing, depth and length

### Slice columns (alignment positions)

```python
from frankenmsa.utils.msatools import slice_sequences

sliced = slice_sequences(msa, start=10, end=120)
```

Crops every sequence to positions 10-120. Assign to a new variable when you want
to keep the original for comparison.

### Slice rows (sequences)

```python
from frankenmsa.utils.msatools import slice_rows

subset = slice_rows(msa, start=0, end=500)      # end=None runs to the last row
```

### Set the depth

```python
from frankenmsa.utils.msatools import adjust_depth, crop_to_depth, extend_to_depth

resized = adjust_depth(msa, depth=512)          # crops or duplicates as needed
smaller = crop_to_depth(msa, depth=512)         # only ever drops rows
larger = extend_to_depth(msa, depth=512)        # only ever repeats rows
```

`adjust_depth` moves in whichever direction is needed. The one-directional pair
is safer when you want a guarantee: `crop_to_depth` returns the MSA unchanged if
it is already shallower than `depth`, and `extend_to_depth` returns it unchanged
if it is already deeper.

Reaching a target depth by duplication adds no new information. Say so if the
user seems to expect real sequences.

### Unify sequence length

```python
from frankenmsa.utils.msatools import unify_length

unify_length(msa, "first")    # crop or pad everything to the query's length
unify_length(msa, "max")      # pad everything to the longest sequence
unify_length(msa, "min")      # crop everything to the shortest
unify_length(msa, 250)        # or an explicit length
```

Padding uses `-`; cropping truncates from the right.

## Editing residues

### Whole-MSA character operations

```python
from frankenmsa.utils.msatools import (
    replace_insertions_with_gaps,   # lowercase insertion characters -> '-'
    replace_unknown_with_gaps,      # 'X' -> '-'
    uppercase_sequences,
    lowercase_sequences,
)
```

In A3M, lowercase marks an insertion relative to the query, so uppercasing
*changes what the alignment means* rather than just how it looks. Use
`replace_insertions_with_gaps` to get a clean aligned block, and
`uppercase_sequences` only when a downstream tool demands uppercase.

### Insert, replace, remove

```python
from frankenmsa.utils.msatools import insert_at, replace_at, remove_at

insert_at(msa, sequence="ACGT", index=10, include_query=True)
replace_at(msa, index=10, replacement="ACGT", include_query=False)
remove_at(msa, start=10, end=20, include_query=True)
```

`insert_at` shifts existing residues right, `replace_at` overwrites in place and
keeps the length, and `remove_at` deletes a slice (`end=None` removes the single
position at `start`).

The `include_query` defaults differ: `insert_at` and `remove_at` include the
query, `replace_at` does not. Excluding the query from an insert or a removal
leaves the query at its original length while every other sequence changes,
which misaligns the MSA — that is almost never what you want.

### Fix positions to the query

```python
from frankenmsa.utils.msatools import fix_at

fixed = fix_at(msa, indices=[0, 5, 10, 11, 12, 13, 14, 15])
```

Copies the query's residues into every other sequence at the given positions,
which is how you force a motif to be conserved across the whole MSA.

Expanding a human-friendly range string such as `"0, 5, 10-15"`:

```python
def parse_indices(text):
    indices = set()
    for part in (p.strip() for p in text.split(",")):
        if not part:
            continue
        if "-" in part:
            lo, hi = (int(x) for x in part.split("-", 1))
            indices.update(range(lo, hi + 1))
        else:
            indices.add(int(part))
    return sorted(indices)
```

## Multimer chains

```python
from frankenmsa.utils.msatools import split_chains, merge_chains

per_chain = split_chains(multimer_msa)     # list of DataFrames, one per chain
multimer = merge_chains(per_chain)         # back into one frame with a `chain` column
```

`split_chains` needs a `_multimer_header` column, which
`frankenmsa.utils.fileio.read_a3m_with_chains` adds when it loads a multimer
file. For splitting a file on disk, or for building a multimer in the first
place, see `download.md`.

## Inspecting

```python
from frankenmsa.utils.msatools import head, tail
from frankenmsa.utils.seqtools import consensus_sequence

head(msa, n=5)                        # first n rows
tail(msa, n=5)                        # last n rows
consensus_sequence(msa["sequence"])   # most common residue per position
```

Plain pandas covers the rest — `len(msa)` for the depth,
`msa["sequence"].str.len()` for the lengths, `msa["sequence"].str.count("-")`
for the gaps. Reporting these before and after an operation is the quickest way
to notice a filter that removed everything.

## Combining MSAs

```python
from frankenmsa.utils.msatools import combine_msa_operations, build_combined_msa_name

combined = combine_msa_operations(
    msas=[msa_a, msa_b],
    directions=["horizontal", "vertical"],
    horizontal_ranges=[(0, 100), (0, 80)],   # column slice per input
    vertical_ranges=[(0, 500), (0, 500)],    # row slice per input
)
```

`"horizontal"` concatenates sequences side by side, producing longer sequences
as for a chimera; `"vertical"` stacks more sequences on top of each other,
producing a deeper MSA. The ranges apply per input before combining, so a single
call covers "take the first 100 columns of A and glue the first 80 of B onto
it".

The two axes fail in different ways, and both failures are silent:

- **Horizontal** needs the inputs to have the same number of rows, and needs the
  column ranges to mean the same positions in every input. See
  [matching depths](#matching-depths-before-a-horizontal-combine) and
  [splicing segments](#splicing-segments-from-several-msas).
- **Vertical** needs one query to win, and needs the stacked rows to land in that
  query's columns. See
  [keeping one query](#keeping-one-query-when-stacking-msas-vertically).

`build_combined_msa_name(msa_data, name)` generates a non-clashing name when you
are keeping several MSAs in a dict.

### Matching depths before a horizontal combine

A horizontal combine glues sequences together row by row, so the inputs need the
same number of rows. If they differ, `combine_msa_operations` quietly calls
`adjust_depth` on the later MSA to match the first one — trimming or repeating
without saying so. Decide the strategy yourself instead, and report it.

**No target depth given** — pad the shallower MSAs with all-gap rows. Every real
sequence survives, and the padding is visibly empty rather than a duplicate
pretending to be data:

```python
import pandas as pd

def pad_with_gap_rows(msa, depth):
    """Grow an MSA to `depth` rows by appending all-gap rows."""
    missing = depth - len(msa)
    if missing <= 0:
        return msa.reset_index(drop=True)
    width = int(msa["sequence"].str.len().max())
    filler = pd.DataFrame({
        "header": [f"gap_padding_{i + 1}" for i in range(missing)],
        "sequence": ["-" * width] * missing,
    })
    return pd.concat([msa, filler], ignore_index=True)

depth = max(len(m) for m in msas)
msas = [pad_with_gap_rows(m, depth) for m in msas]
print(f"no depth given: padded every MSA to {depth} rows with gap-only rows")
```

**A target depth given** — put each MSA through `to_depth` from the HHfilter
section above, which uses hhfilter to pick a diverse subset and then corrects
the overshoot or shortfall:

```python
msas = [to_depth(m, depth, label=name) for name, m in zip(names, msas)]
```

**Without hh-suite** — `to_depth` already falls back to keeping the first
`depth` rows, or repeating to fill, and says which it did.

Whichever route is taken, tell the user: padding keeps every sequence but
dilutes the alignment with gaps, hhfilter keeps a diverse subset but discards
sequences, and repeating inflates the depth without adding information. Those
are different trade-offs and the choice should not be invisible.

### Splicing segments from several MSAs

The common way to build a chimera is to take successive stretches of one chain
from different MSAs: positions 0-10 from MSA A, 11-26 from MSA B, 26-60 from A
again. The ranges are positions of **one shared query**, so each MSA has to be
read in that query's numbering rather than its own.

That is where it goes wrong. An MSA's columns are positions of *its own* query,
and two MSAs of the same protein rarely agree: a construct tag, a leading
methionine or a slightly different construct shifts one against the other.
Slicing each MSA by the raw index then takes the wrong residues:

```
reference query  ACDEFGHIKL        positions 4-6 are FGH
MSA B's query   XACDEFGHIKL        its own columns 4-6 are EFG   <- off by one
```

So fix a reference query, map every other MSA onto it, and cut the ranges in
that frame. Equalise depths first — a horizontal splice joins row *i* of each
segment, so the segments need the same number of rows; see the section above.

```python
import pandas as pd
from Bio.Align import PairwiseAligner


def reference_to_msa_map(ref_query, msa_query):
    """Reference query position -> column of this MSA."""
    aligner = PairwiseAligner(mode="global", match_score=2, mismatch_score=-1,
                              open_gap_score=-10, extend_gap_score=-0.5)
    best = aligner.align(ref_query.upper(), msa_query.upper())[0]
    mapping = {}
    for (r_start, r_end), (m_start, m_end) in zip(*best.aligned):
        for off in range(r_end - r_start):
            mapping[r_start + off] = m_start + off
    return mapping


def stitch_segments(segments, reference=None, depth=None):
    """Splice column ranges of several MSAs into one chimeric chain.

    segments  : list of (msa, start, end); ranges are positions of the
                reference query, end exclusive.
    reference : MSA whose query numbering the ranges use (default: the first).
    """
    prepared = [(to_query_columns(m), start, end) for m, start, end in segments]
    ref = to_query_columns(reference) if reference is not None else prepared[0][0]
    ref_query = ref["sequence"].iloc[0]

    if depth is None:
        depth = max(len(m) for m, _, _ in prepared)
        print(f"no depth given: padding every segment to {depth} rows with gap-only rows")
    prepared = [(pad_with_gap_rows(m, depth), s, e) for m, s, e in prepared]

    columns = []
    print("stitched in the reference query's numbering:")
    for i, (msa, start, end) in enumerate(prepared):
        msa_query = msa["sequence"].iloc[0]
        if msa_query.upper() == ref_query.upper():
            mapping, how = {p: p for p in range(len(ref_query))}, "same query"
        else:
            mapping = reference_to_msa_map(ref_query, msa_query)
            identity = mapped_identity(ref_query, msa_query, mapping)
            how = (f"aligned to the reference "
                   f"({len(mapping)}/{len(ref_query)} positions mapped, "
                   f"{identity:.0%} identical)")

        unmapped = [p for p in range(start, end) if p not in mapping]
        columns.append([
            "".join(seq[mapping[p]] if p in mapping and mapping[p] < len(seq) else "-"
                    for p in range(start, end))
            for seq in msa["sequence"]
        ])
        print(f"  [{start}:{end}) from segment {i} - {how}"
              + (f", {len(unmapped)} position(s) unmapped -> gaps" if unmapped else ""))

    out = prepared[0][0].iloc[:depth].reset_index(drop=True).copy()
    out["sequence"] = ["".join(parts) for parts in zip(*columns)]
    return out
```

`to_query_columns`, `pad_with_gap_rows` and `mapped_identity` are the helpers
from the sections above. Calling it on the example:

```python
stitch_segments([(A, 0, 4), (B, 4, 7), (A, 7, 10)])
```

takes `ACDE` from A, then B's residues at reference positions 4-6 — B's own
columns 5-7, not 4-6 — then `IKL` from A, so the query row comes out as the
intended `ACDEFGHIKL` and every homolog row is cut at the same boundaries.

Ranges may revisit the same MSA as often as needed, and each segment keeps the
residues of the MSA it came from, which is the point of a chimera: positions
4-6 carry B's sequence, read in A's numbering.

Report the layout, and read the per-segment **identity** rather than the number
of mapped positions. A global alignment maps two unrelated sequences of the same
length end to end, so coverage alone looks perfect either way; identity is what
reveals that a segment is being cut from the wrong protein.

### Keeping one query when stacking MSAs vertically

**This section is for vertical stacking only** — making one MSA deeper by
putting the sequences of another underneath it. To build a longer chimeric
chain out of column ranges, see
[splicing segments](#splicing-segments-from-several-msas) instead.

Every MSA carries its own query in row 0, and the columns of an MSA mean
positions *of that query*. Stacking two MSAs with `pd.concat` or a vertical
combine therefore does two things the user rarely wants: the combined MSA ends
up with a second query row partway down, and if the two queries differ at all —
a leading residue, a construct tag, a slightly different construct — every
stacked row is offset against the columns it lands in.

```
query A   ACDEFGHIK          naive stack        ACDEFGHIK   <- qA
query B    CDEFGHIKL                            ACDEFGHIR
                                                CDEFGHIKL   <- qB, a second query
                                                CDEFGHIKM   <- C now sits under A
```

So when combining MSAs of the same chain, ask which query should persist, align
the other queries to it, and drop the duplicates. Report the choice, because the
kept query defines the coordinates of everything downstream.

```python
import pandas as pd
from Bio.Align import PairwiseAligner


def to_query_columns(msa):
    """Keep only the columns where this MSA's own query has a residue."""
    query = msa["sequence"].iloc[0]
    keep = [i for i, ch in enumerate(query) if ch != "-"]
    out = msa.copy()
    out["sequence"] = [
        "".join(seq[i] if i < len(seq) else "-" for i in keep)
        for seq in msa["sequence"]
    ]
    return out


def query_position_map(kept_query, other_query):
    """Map each position of other_query onto a position of kept_query."""
    aligner = PairwiseAligner(mode="global", match_score=2, mismatch_score=-1,
                              open_gap_score=-10, extend_gap_score=-0.5)
    best = aligner.align(kept_query.upper(), other_query.upper())[0]
    mapping = {}
    for (k_start, k_end), (o_start, o_end) in zip(*best.aligned):
        for offset in range(k_end - k_start):
            mapping[o_start + offset] = k_start + offset
    return mapping


def mapped_identity(key_seq, value_seq, mapping):
    """Fraction of mapped positions where the two queries agree.

    `mapping` sends positions of `key_seq` to positions of `value_seq`, so pass
    the two sequences in that order.

    A global aligner lines up any two sequences of similar length, so the number
    of mapped positions says nothing about whether they are the same protein.
    Identity does.
    """
    if not mapping:
        return 0.0
    same = sum(key_seq[k].upper() == value_seq[v].upper()
               for k, v in mapping.items())
    return same / len(mapping)


def stack_on_query(msas, keep=0):
    """Stack MSAs vertically in the coordinate frame of msas[keep]'s query."""
    msas = [to_query_columns(m) for m in msas]
    anchor = msas[keep]
    anchor_query = anchor["sequence"].iloc[0]
    width = len(anchor_query)
    frames = [anchor]

    for i, msa in enumerate(msas):
        if i == keep:
            continue
        other_query = msa["sequence"].iloc[0]
        if other_query.upper() == anchor_query.upper():
            print(f"MSA {i}: identical query, stacked directly")
            frames.append(msa.iloc[1:])
            continue

        mapping = query_position_map(anchor_query, other_query)
        identity = mapped_identity(other_query, anchor_query, mapping)
        print(f"MSA {i}: query differs, aligned to the kept query "
              f"({len(mapping)}/{len(other_query)} positions mapped, "
              f"{identity:.0%} identical)")
        remapped = []
        for seq in msa["sequence"]:
            chars = ["-"] * width
            for o_pos, k_pos in mapping.items():
                if o_pos < len(seq):
                    chars[k_pos] = seq[o_pos]
            remapped.append("".join(chars))
        shifted = msa.copy()
        shifted["sequence"] = remapped
        frames.append(shifted.iloc[1:])

    print(f"kept the query of MSA {keep}; "
          f"dropped {len(msas) - 1} duplicate query row(s)")
    return pd.concat(frames, ignore_index=True)
```

On the example above, `stack_on_query([A, B], keep=0)` puts B's rows into A's
frame — `CDEFGHIKM` becomes `-CDEFGHIK` — and leaves a single query at the top.
Passing `keep=1` reframes everything into B's coordinates instead, which is how
the user chooses whose numbering the result uses.

`PairwiseAligner` comes from biopython, which the ProteinMPNN and GhostFold
installers pull in; otherwise `pip install biopython`. The identical-query path
needs no alignment, so MSAs built from the same query sequence stack without it.

Positions of the other query that find no match are dropped. Watch the reported
**identity**, not the number of mapped positions: a global alignment lines up
any two sequences of similar length, so two unrelated queries still map
end to end. Identity near 100% means the same protein with a shift; a low
identity means stacking them is probably a mistake.
