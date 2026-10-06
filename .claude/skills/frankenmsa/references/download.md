# Reading and writing MSAs, and building multimers

All functions live in `frankenmsa.utils.fileio`, and the common ones are
re-exported from `frankenmsa.utils`.

## Contents

- [Choosing a format](#choosing-a-format)
- [Reading](#reading)
- [Writing](#writing)
- [Building a multimer MSA](#building-a-multimer-msa)
- [The multimer A3M format](#the-multimer-a3m-format)
- [Splitting a multimer into chains](#splitting-a-multimer-into-chains)

## Choosing a format

| Format | Keeps extra columns | Use for |
|---|---|---|
| `.a3m` | no | folding models; the usual output |
| `.fasta` / `.fa` | no | interchange with other tools |
| `.csv` | **yes** | anything carrying `cluster_id`, `ward_id` or `chain` |

A3M and FASTA store only the header and the sequence. Write CSV whenever the
result of clustering or chain assignment has to survive the round trip,
otherwise those columns are dropped without warning.

## Reading

```python
from frankenmsa.utils import read_a3m
from frankenmsa.utils.fileio import read_a3m_with_chains, decode_a3m, read_fasta
import pandas as pd

msa = read_a3m("input.a3m")                 # A3M or FASTA -> header, sequence
msa = read_a3m_with_chains("input.a3m")     # adds a `chain` column for multimers
msa = decode_a3m(a3m_text)                  # the same, from a string in memory
msa = pd.read_csv("input.csv")              # needs at least a `sequence` column
sequences, descriptions = read_fasta(text)  # multi-record FASTA -> two lists
```

`read_a3m_with_chains` is the forgiving choice when the file's origin is
unknown: on a monomer it behaves like `read_a3m`, and on a multimer it stacks
the chains with a `chain` column and keeps the original header line in
`_multimer_header`.

To branch on the content before loading:

```python
from frankenmsa.utils.fileio import is_multimer_a3m_text
is_multimer_a3m_text(open("input.a3m").read())    # True for a multimer A3M
```

## Writing

```python
from frankenmsa.utils import write_a3m
from frankenmsa.utils.fileio import encode_a3m, write_fasta

write_a3m(msa, "output.a3m")
msa.to_csv("output.csv", index=False)       # keeps cluster_id and friends
text = encode_a3m(msa)                      # the same content as a string
```

## Building a multimer MSA

A multimer MSA tells a folding model that several chains form one complex.
There are three ways to make one and they are **not interchangeable** — pick by
whether the chains need to be paired, that is matched row by row across chains,
usually by species.

### Unpaired: stack independent chain MSAs

The right choice when each chain has its own MSA and no species correspondence
exists between them.

```python
from frankenmsa.utils import write_a3m
from frankenmsa.utils.fileio import combine_unpaired_a3m

write_a3m(chain_a, "A.a3m")
write_a3m(chain_b, "B.a3m")
combine_unpaired_a3m(["A.a3m", "B.a3m"], "complex.a3m")
```

Input order sets the chain order: the first file becomes chain A, the second
chain B, and so on. `chain_label(i)` gives the label for position `i` (A-Z, then
AA, AB, ...). Listing the same MSA twice builds a homodimer.

Chains may have different depths; each keeps all of its sequences.

For CSV instead, directly from a dict of MSAs:

```python
from frankenmsa.utils.fileio import build_multimer_csv

df = build_multimer_csv(
    {"A": chain_a.to_dict("list"), "B": chain_b.to_dict("list")},
    ["A", "B"],
)
df.to_csv("complex.csv", index=False)       # header, sequence, chain
```

### Paired: one MMseqs2 query

The right choice when the chains are expected to co-evolve and matched species
rows matter, which is what AlphaFold-Multimer makes use of. Join the chains with
`:` in a single query and choose a pairing mode:

```python
from frankenmsa.align import LocalMMSeqs2Colab

msa_df, header_str, chain_lengths = LocalMMSeqs2Colab().align("AAAA:CCCC", "complete")
```

See `align.md`. Stacking independently searched chains cannot produce paired
rows, so this is the only route to a genuinely paired complex.

### Fused: one longer chain

Horizontal concatenation joins the sequences end to end, producing a single
chain of combined length with no chain header. A folding model reads that as one
polypeptide — a chimera rather than a complex.

```python
from frankenmsa.utils.msatools import combine_msa_operations

fused = combine_msa_operations([msa_a, msa_b], ["horizontal", "horizontal"])
```

See `edit.md`.

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
which is what makes the file unpaired: rows carry no correspondence across
chains. The leading `#` line is what `is_multimer_a3m_text` recognises.

Within a chain, shorter sequences are right-padded with `-` so each block is
rectangular.

### The anchor row

`add_anchor=True`, the default, writes the concatenated query of all chains as
the first record. Folding models expect that full-length query, so keep it for
anything you intend to fold.

Pass `add_anchor=False` for a file you plan to split again. The anchor is
distributed back into every chain on splitting, which would otherwise leave each
chain with a duplicate query row:

```python
combine_unpaired_a3m(paths, "intermediate.a3m", add_anchor=False)
```

## Splitting a multimer into chains

```python
from frankenmsa.utils.fileio import split_multimer_a3m_file, split_dataframe_by_chain

chains = split_multimer_a3m_file("complex.a3m", "job")   # {"jobA": df, "jobB": df}
chains = split_dataframe_by_chain(csv_df, "job")         # the same, via a `chain` column
```

Both return a dict keyed by `{base_name}{chain_label}`, so a complex becomes
several ordinary single-chain MSAs that every tool in `edit.md` accepts.

`frankenmsa.utils.msatools.split_chains` and `merge_chains` do the same job on
an in-memory DataFrame that carries `_multimer_header`; see `edit.md`.
