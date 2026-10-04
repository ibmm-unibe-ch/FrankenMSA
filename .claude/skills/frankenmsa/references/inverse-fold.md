# Inverse folding with ProteinMPNN

Generates sequences predicted to fold into a given structure. Collect four
things before running: **which structure**, **which chains**, **how many
sequences**, **what temperature**.

Check availability first (`resolve_proteinmpnn_root()`, see `install.md`) — a
missing checkout produces a long traceback that is hard to read.

```python
from frankenmsa.inverse_fold import run_proteinmpnn

result = run_proteinmpnn(
    pdb_code="2NNC",          # downloaded from RCSB into ~/.frankenmsa/pdb_cache
    # pdb_path="/path/to/structure.pdb",   # ... or a local file
    num_seqs=128,
    sampling_temp=1.0,
    homomer=True,
    design_chains="",         # "A" or "A,B"; empty = all
    fixed_chains="",          # "B"; kept at native sequence
    model_name="v_48_020",
    use_soluble_model=False,
    ca_only=False,
    runtime="local",          # "colab" provisions the checkout on the fly
    clean_workspace=False,
)
print(result["a3m"], result["num_sequences"], result["cuda_available"])
```

## Structure input

`pdb_path` wins over `pdb_code` when both are set. With neither, the call raises
`RuntimeError` asking for one, so resolve this with the user first.

- `pdb_code` — a four-character RCSB code, downloaded with retries and cached in
  `~/.frankenmsa/pdb_cache` (`/content` on Colab). Case-insensitive.
- `pdb_path` — a local `.pdb` or `.cif`. The file is staged into the ProteinMPNN
  output directory before the run.

`download_pdb_by_code(code, target_dir=None)` is available separately if you just
want the file.

## Chains

`homomer=True` designs every chain with a single tied sequence and **ignores
`design_chains` and `fixed_chains` entirely**. That is correct for a homomer and
silently wrong for a complex of different chains.

For a heteromer set `homomer=False` and name the chains:

- `design_chains` — redesigned.
- `fixed_chains` — kept at their native sequence, used as context.

Chain lists are comma-separated single letters (`"A,B"`). The parser uppercases,
accepts `;` as a separator, and **drops anything that is not a single letter**,
so `"chain A"` silently becomes empty. With `design_chains` empty, all chains are
designed.

Under the hood a heteromer run uses ProteinMPNN's `parse_multiple_chains.py` and
`assign_fixed_chains.py` helper scripts when they exist in the checkout, falling
back to a hand-written `chain_id.jsonl`.

### Positions

This entry point designs **whole chains, not individual residues**. If a user
asks to redesign only positions 45-60, say that this interface cannot do it
rather than quietly designing the whole chain. (ProteinMPNN itself supports
fixed-position JSONL files; using them means calling `protein_mpnn_run.py`
directly with a `--fixed_positions_jsonl`.)

To constrain positions *after* generating, `frankenmsa.utils.msatools.fix_at`
can propagate the query's residues back into chosen positions — see `edit.md`.

## Count and temperature

- `num_seqs` (default 128) — how many sequences to sample.
- `sampling_temp` (default 1.0) — diversity. Low (0.1-0.3) stays close to the
  native sequence; above 1.0 explores further and risks less plausible
  sequences.

"More diverse sequences" could mean either knob, so ask which. Without a GPU the
run falls back to CPU and large `num_seqs` gets slow — check
`result["cuda_available"]` and warn when it is `False` and the user asked for
thousands.

## Model variants

- `model_name` — default `"v_48_020"`, the weight set the installer fetches.
- `use_soluble_model=True` — the soluble-protein weights.
- `ca_only=True` — the Cα-only model, for backbones without full atom detail.

Each variant reads from its own weight directory; the installer downloads all
three.

## Results

`run_proteinmpnn` returns a dict:

| Key | What |
|---|---|
| `a3m` / `a3m_path` / `a3m_text` | generated sequences as A3M, ready to load as an MSA |
| `fasta` | the merged FASTA |
| `zip` | all raw outputs zipped |
| `num_sequences` | how many were actually produced |
| `split_chains` | per-chain FASTAs when the output had a chain separator |
| `cuda_available` | whether the run used a GPU |
| `pdb_path`, `out_dir`, `weights_root`, `model_name` | provenance |
| `designed_chains`, `fixed_chains`, `homomer`, `sampling_temp`, `num_seqs` | echoed settings |

Load the result as an MSA with
`frankenmsa.utils.read_a3m(result["a3m"])`, or
`frankenmsa.utils.fileio.decode_a3m(result["a3m_text"])` to skip the file.

## Runtime

`runtime="local"` expects an installed checkout and writes to `outputs_local`
inside it. `runtime="colab"` provisions ProteinMPNN if missing, writes to
`outputs_run`, and puts the ZIP in `/content`. Anything else raises
`ValueError`. `clean_workspace=True` clears previous outputs first — useful
between runs, destructive if earlier results have not been collected.
