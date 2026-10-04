# Augmentation with GhostFold

GhostFold generates a pseudo-MSA for a single sequence. It is the tool for the
case where normal alignment returns almost nothing — an orphan sequence, a
designed protein, a fast-evolving family — and a folding model still needs an
MSA to work with.

Check availability first:

```python
from frankenmsa.augment.ghostfold import resolve_ghostfold_command

try:
    command = resolve_ghostfold_command()   # FileNotFoundError if absent
except FileNotFoundError:
    ...  # offer: python scripts/installers/install_ghostfold.py
```

## Running it

```python
from frankenmsa.augment import run_ghostfold_augmentation

msa_data, key, created_keys, msa_df = run_ghostfold_augmentation(user_text, msa_data)
```

Or, when not using the app's store:

```python
from frankenmsa.augment import GhostFold
from frankenmsa.augment.workflows import normalize_ghostfold_input

sequence = normalize_ghostfold_input(user_text)
msa_df = GhostFold().augment(sequence=sequence)
```

Results are stored as `ghostfold_aug_1`, `ghostfold_aug_2`, ... by
`build_ghostfold_result_key`.

## Input rules

All four raise `ValueError` from `normalize_ghostfold_input`, so validate before
running rather than letting the error surface mid-run:

1. **Exactly one sequence.** Two or more FASTA records are rejected, not merged.
2. **A monomer.** A `:` chain separator is rejected.
3. **Amino-acid letters only** after whitespace is stripped and case is raised.
4. **Not empty.**

A single FASTA record is fine — the header is dropped. This is stricter than the
MMseqs2 input handling, which silently concatenates multiple records.

## No parameters

GhostFold takes no count, no temperature, no database. The tool decides how many
sequences it produces. If a user asks for "100 GhostFold sequences", explain
that this is not a knob — then, if they need a specific depth, point at
`frankenmsa.utils.msatools.adjust_depth` to resize the result afterwards
(noting that padding duplicates existing rows rather than adding information).

## When a run fails

`GhostFold.augment` writes the input to a temporary FASTA, shells out to the
cloned `ghostfold.sh` (or the `ghostfold` CLI), and reads back
`msa/*/pstMSA.a3m` from the project directory. Failures surface as:

- `subprocess.CalledProcessError` — the script exited non-zero. stdout and
  stderr go to the FrankenMSA log (`log.txt` at the repo root, or
  `/content/app/log.txt` on Colab); that is where the real error is.
- `FileNotFoundError: GhostFold did not produce a pseudoMSA under ...` — the run
  succeeded but wrote nothing, usually an input the tool could not handle.

Runs take a while; it is a real folding-adjacent pipeline, not an API call. Say
so before starting one rather than letting it look hung.
