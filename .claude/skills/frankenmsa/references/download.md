# Loading and exporting MSAs, and building multimers

Everything the Files page does. This is also where **multimer MSAs are
assembled**, because a multimer is built by exporting several single-chain MSAs
together.

All functions are in `frankenmsa.utils.fileio` (re-exported from
`frankenmsa.utils`).

## Contents

- [Formats](#formats)
- [Loading](#loading)
- [Exporting a single MSA](#exporting-a-single-msa)
- [Making a multimer MSA](#making-a-multimer-msa)
- [The multimer A3M format](#the-multimer-a3m-format)
- [Splitting a multimer back into chains](#splitting-a-multimer-back-into-chains)
- [Pitfalls](#pitfalls)

## Formats

| Format | Keeps extra columns | Use for |
|---|---|---|
| `.a3m` | no | folding models; the default |
| `.fasta` / `.fa` | no | interchange |
| `.csv` | **yes** | anything with `cluster_id`, `ward_id` or `chain` that must survive |

A3M and FASTA store only header and sequence. **Export to CSV whenever the
result of clustering or chain assignment needs to be preserved** — otherwise
those columns are silently dropped on write.

## Loading

```python
from frankenmsa.utils import read_a3m
from frankenmsa.utils.fileio import read_a3m_with_chains, decode_a3m, read_fasta
import pandas as pd

msa = read_a3m("input.a3m")                 # monomer A3M/FASTA -> header, sequence
msa = read_a3m_with_chains("input.a3m")     # detects multimers, adds a `chain` column
msa = decode_a3m(a3m_text)                  # same, from a string in memory
msa = pd.read_csv("input.csv")              # needs at least a `sequence` column
sequences, descriptions = read_fasta(text)  # multi-record FASTA -> two lists
```

`read_a3m_with_chains` is the forgiving entry point: on a monomer it behaves like
`read_a3m`, and on a ColabFold-style multimer it returns the chains stacked with
a `chain` column plus `_multimer_header` carrying the original header line.

To check before loading:

```python
from frankenmsa.utils.fileio import is_multimer_a3m_text
is_multimer_a3m_text(open("input.a3m").read())   # True if it starts with the # header
```

The GUI accepts `.a3m`, `.fasta`, `.fa` and `.csv` up to 50 MB, and refuses a
CSV without a `sequence` column.

## Exporting a single MSA

```python
from frankenmsa.utils import write_a3m
from frankenmsa.utils.fileio import encode_a3m, write_fasta

write_a3m(msa, "output.a3m")
msa.to_csv("output.csv", index=False)      # keeps cluster_id etc.
text = encode_a3m(msa)                     # same content as a string
```

## Making a multimer MSA

A multimer MSA tells a folding model "these chains form one complex". There are
three routes, and they are **not interchangeable**:

### 1. Unpaired — stack independent chain MSAs (the Files page)

Use when each chain has its own MSA and you have no species correspondence
between them. This is what the Files page does when you add several MSAs to the
export list.

```python
from frankenmsa.utils import write_a3m
from frankenmsa.utils.fileio import combine_unpaired_a3m

write_a3m(chain_a, "A.a3m")
write_a3m(chain_b, "B.a3m")
combine_unpaired_a3m(["A.a3m", "B.a3m"], "complex.a3m")
```

Order matters: the first input becomes chain A, the second chain B, and so on
(`chain_label(i)` gives the label for position `i`: A-Z, then AA, AB, ...). The
same MSA may be listed twice to build a homodimer.

For CSV instead, straight from the store:

```python
from frankenmsa.utils.fileio import build_multimer_csv
df = build_multimer_csv({"A": chain_a.to_dict("list"), "B": chain_b.to_dict("list")}, ["A", "B"])
df.to_csv("complex.csv", index=False)      # header, sequence, chain
```

### 2. Paired — one MMseqs2 query (the Align page)

Use when the chains are expected to co-evolve and matched species rows matter,
which is what AlphaFold-Multimer benefits from. Join the chains with `:` in a
single query and pick a pairing mode:

```python
from frankenmsa.align import LocalMMSeqs2Colab
msa_df, header_str, chain_lengths = LocalMMSeqs2Colab().align("AAAA:CCCC", "complete")
```

See `align.md`. This produces genuinely paired rows; route 1 cannot, because the
chains were searched independently.

### 3. Horizontal concatenation (the Combine page)

Use when you want to fuse sequences into one longer chain rather than declare
separate chains — a chimera, not a complex:

```python
from frankenmsa.utils.msatools import combine_msa_operations
fused = combine_msa_operations([msa_a, msa_b], ["horizontal", "horizontal"])
```

This yields one chain of combined length with no chain header, so a folding
model treats it as a single polypeptide. See `edit.md`.

## The multimer A3M format

`combine_unpaired_a3m` writes the ColabFold convention:

```
#4,6	1,1            <- chain lengths, then copy counts, tab-separated
>101	102            <- anchor: the concatenated query of every chain
AAAACCCCCC
>qA
AAAA------            <- chain A rows, right-padded with gaps
>a1
AAAC------
>qB
----CCCCCC            <- chain B rows, left-padded with gaps
>b1
----CCCCCA
```

Each chain occupies its own block of columns and is gap-padded everywhere else,
which is what "unpaired" means structurally. The `#` line is what
`is_multimer_a3m_text` detects.

`add_anchor=True` (the default) writes the concatenated query row. Keep it for
folding models, which expect the full-length query first.

## Splitting a multimer back into chains

```python
from frankenmsa.utils.fileio import split_multimer_a3m_file, split_dataframe_by_chain

chains = split_multimer_a3m_file("complex.a3m", "job")   # {"jobA": df, "jobB": df}
chains = split_dataframe_by_chain(csv_df, "job")         # same, from a `chain` column
```

Both return a dict keyed by `{base_name}{chain_label}`. The GUI does this
automatically on upload and selects the first chain, so a multimer file becomes
several editable MSAs.

## Pitfalls

**Unequal depths are fine, but check your version.** Chains may differ in depth:
each one keeps all of its sequences, and the splitter reads them back correctly.
Earlier versions truncated every chain to the shallowest one — a 5000-sequence
chain exported beside a 200-sequence partner lost 96% of its alignment, warning
only with a `print()` to stdout that the GUI never showed. That block is
commented out in `combine_unpaired_a3m` (`frankenmsa/utils/fileio.py`). If you
are on a version where it is still active, the symptom is every chain coming
back at the same depth:

```python
depths = [len(c) for c in (chain_a, chain_b)]
print(f"input depths: {depths}")   # compare against the exported file
```

**The round-trip is not lossless.** Combining with the anchor and splitting again
returns the query twice, because the anchor row is distributed back into each
chain. Use `add_anchor=False` when the file is an intermediate you will split
again, or `drop_duplicates` afterwards:

```python
combine_unpaired_a3m(paths, "intermediate.a3m", add_anchor=False)
```

**Sequences are padded to the chain's longest.** Within each chain, shorter
sequences are right-padded with `-` before combining, so ragged input becomes a
rectangular block.

**Chain order is the export order**, not alphabetical and not the order the MSAs
were created. Build the list deliberately.
