# Generating an MSA: MMseqs2 and PLM-Search

Both search remote services for relatives of a query sequence. They answer
different questions:

- **MMseqs2** (ColabFold API) finds homologs by sequence similarity and returns a
  true alignment. This is what you want as folding-model input.
- **PLM-Search** finds sequences with similar protein-language-model embeddings,
  catching remote relatives that sequence search misses — but it returns
  *similar sequences, not an alignment*.

Both hit public servers, so they need network access and can fail or rate-limit.

When the user names a PDB ID instead of pasting a sequence, pull the query from
RCSB first with `frankenmsa.utils.download_fasta` — see `download.md`.

## MMseqs2

```python
from frankenmsa.align import MMSeqs2Colab, LocalMMSeqs2Colab
from frankenmsa.align.workflows import normalize_mmseqs_input, validate_mmseqs_request

sequence = normalize_mmseqs_input(user_text)
is_multimer = validate_mmseqs_request(sequence, pairing_mode)

if is_multimer:
    msa_df, header_str, chain_lengths = LocalMMSeqs2Colab().align(sequence, pairing_mode)
else:
    msa_df = MMSeqs2Colab("my-job").align([sequence], True, filter_mode, None)
```

Note the two different classes: `MMSeqs2Colab` for monomers, `LocalMMSeqs2Colab`
for the paired multimer endpoint. The monomer `align` signature is
`align(sequences, env=True, filter=True, pairing=None, save_to=None, retries=3, timeout=10, cleanup=True)`.

### Input

`normalize_mmseqs_input` drops FASTA header lines, strips whitespace and
uppercases, then returns **one** string. A single-record FASTA works fine. A
multi-record FASTA is silently concatenated into one long sequence, so run
separate queries per record.

### Pairing mode

The mode must agree with whether the sequence contains `:`, and
`validate_mmseqs_request` raises `ValueError` when it does not:

| Mode | Use for | Meaning |
|---|---|---|
| `"none"` | monomer (no `:`) | no pairing |
| `"greedy"` | multimer | one best match per species; strict, often returns empty from the public server |
| `"complete"` | multimer | all matches per species; the better default for a complex |

`AAAA:BBBB` is a two-chain complex. Mixing them up is the most common error:
`:` with `"none"`, or no `:` with `"greedy"`/`"complete"`, both raise.

### Filtering

`filter=True` (the default) removes low-complexity regions. It applies only
to the monomer path — the multimer endpoint does not take it.

### Splitting a multimer result

The multimer call returns one combined MSA plus the per-chain lengths. To get
the chains separately:

```python
from frankenmsa.utils.seqtools import multimer_chain_splitting
message, msa_data = multimer_chain_splitting(msa_df, chain_lengths, key, msa_data)
```

## PLM-Search

```python
from frankenmsa.align import PLMSearch
from frankenmsa.align.workflows import parse_plm_input, validate_similarity_cutoff

sequences, descriptions = parse_plm_input(user_text)   # proper multi-record FASTA
validate_similarity_cutoff(0.9)                        # raises outside 0.0-1.0

df = PLMSearch().align(
    sequences, descriptions,
    database="uniref50",     # "uniref50" | "PDB" | "Swiss-Prot"
    similarity_cutoff=0.9,
    max_sequences=200,       # per query, not across all queries
)
```

Unlike MMseqs2, PLM-Search takes several queries at once and returns one frame
with a `query` column identifying which query each hit belongs to.

```python
from frankenmsa.align.workflows import attach_plm_search_results
msa_data, main_key, new_keys = attach_plm_search_results(msa_data, df)
```

This splits the frame into one MSA per query, named
`plm_search_{query}_{n}`.

### Choosing the parameters

Hits are enriched with UniProt metadata, which means a low cutoff combined with
a high `max_sequences` turns into a long download. Steer toward a cutoff around
0.9 and a few hundred sequences unless the user has a reason to go wider. The
cutoff is a similarity score in `[0, 1]`, not a percentage identity.

`max_sequences` applies **per input sequence**, so five queries at 200 each is up
to 1000 downloads.

### Before using the result as an MSA

The returned sequences are unaligned. Feeding them straight to a folding model
is usually wrong. At minimum unify the lengths
(`frankenmsa.utils.msatools.unify_length`), or align them properly, before
treating the result as an MSA.

## Storing results

Both paths use the same store helpers:

```python
from frankenmsa.align.workflows import build_result_key, attach_alignment_result

key = build_result_key(msa_data, "mmseqs")          # mmseqs_1, mmseqs_2, ...
msa_data = attach_alignment_result(msa_data, key, msa_df, multimer_header_str=None)
```

When scripting outside the app, skip these and write the DataFrame directly with
`frankenmsa.utils.write_a3m(df, path)`.
