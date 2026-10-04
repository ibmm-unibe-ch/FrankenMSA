# Installing FrankenMSA and its plugins

The base package covers MMseqs2, PLM-Search, AFCluster, KMeans with one-hot
encoding, and every editing operation. Three capabilities need a heavy
dependency that is installed separately, on purpose, so that a user who only
wants alignments does not download model weights.

| Capability | Needs | Installer |
|---|---|---|
| Inverse folding | ProteinMPNN checkout + weights | `install_proteinmpnn.py` |
| GhostFold augmentation | `ghostfold` clone + Python deps | `install_ghostfold.py` |
| KMeans `encoding="esm"` | `esm` package (ESM3) | `install_esm.py` |
| HHfilter | hh-suite binaries | not bundled; conda or system package |

## Base install

```bash
./install.sh            # creates .venv and installs the package editable
source .venv/bin/activate
```

`install.sh` tries `pip install -e .[all]` and falls back to a plain editable
install. Manual setup works too:

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

## The three plugin installers

All live in `scripts/installers/` and are independent of each other, so
"install everything" is just running all three after the base install.

```bash
# ProteinMPNN: clones the repo and fetches v_48_020 weights
# for the vanilla, soluble and ca model variants.
python scripts/installers/install_proteinmpnn.py \
    --root "$HOME/tools/ProteinMPNN" --install-python-deps

# GhostFold: pip-installs deps, clones github.com/rostro36/ghostfold
# into ./ghostfold relative to the current directory, and chmod +x's the script.
python scripts/installers/install_ghostfold.py

# ESM3
python scripts/installers/install_esm.py
```

`install_esm.py` and `install_ghostfold.py` take `--upgrade` to refresh an
existing install. `install_proteinmpnn.py` takes `--ref` to pin a git ref and
`--skip-weight-check` to skip the weight download.

The ProteinMPNN default root is `/content/ProteinMPNN` on Colab and
`./external/ProteinMPNN` otherwise. Since `--root` decides where it lands and
the resolver searches a different set of paths, passing an explicit `--root` and
then setting `FRANKENMSA_PROTEINMPNN_ROOT` to the same value is the least
surprising combination.

## Pointing at an existing install

Both resolvers check environment variables before falling back to conventional
paths, so a user who already has a checkout does not need to install again.

**ProteinMPNN** root, in order: `FRANKENMSA_PROTEINMPNN_ROOT`,
`PROTEINMPNN_LOCAL_ROOT`, `ProteinMPNN_DIR`, then `<repo>/ProteinMPNN`,
`./ProteinMPNN`, `~/ProteinMPNN`. A directory counts as valid only if it
contains `protein_mpnn_run.py` and a `helper_scripts` directory.

**ProteinMPNN weights**: `FRANKENMSA_PROTEINMPNN_WEIGHTS_DIR`,
`PROTEINMPNN_WEIGHTS_DIR`, `FRANKENMSA_PROTEINMPNN_WEIGHTS_ROOT`,
`PROTEINMPNN_WEIGHTS_ROOT`, else the `vanilla_model_weights` /
`soluble_model_weights` / `ca_model_weights` subdirectory of the checkout.

**GhostFold**: `FRANKENMSA_GHOSTFOLD_BIN`, `GHOSTFOLD_BIN`,
`FRANKENMSA_GHOSTFOLD_ROOT`, `GHOSTFOLD_ROOT`, then `ghostfold` on `PATH`, then
`./ghostfold/ghostfold.sh`.

## Checking what is available

```python
from frankenmsa.inverse_fold.protein_mpnn_support import resolve_proteinmpnn_root
from frankenmsa.augment.ghostfold import resolve_ghostfold_command
from frankenmsa.filter.hhsuite import has_hhsuite
import importlib.util

try:
    root = resolve_proteinmpnn_root()      # RuntimeError if absent
except RuntimeError:
    ...

try:
    cmd = resolve_ghostfold_command()      # FileNotFoundError if absent
except FileNotFoundError:
    ...

has_esm = importlib.util.find_spec("esm") is not None
has_hh = has_hhsuite()                     # bool, no exception
```

Run the matching check before a plugin task and offer the install command on
failure rather than letting the run produce a long traceback. These downloads
are large enough that the user should get to decide.

## Programmatic provisioning

`frankenmsa.inverse_fold.provision_proteinmpnn(root=None, install_python_deps=True)`
runs the installer as a subprocess and returns the resolved paths. `run_proteinmpnn`
calls it automatically when `runtime="colab"` and the checkout is missing, which
is how the Colab notebook bootstraps itself. On a local machine it does not
auto-provision — install first.
