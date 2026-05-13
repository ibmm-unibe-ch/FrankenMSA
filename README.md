![](app/assets/frankenmsa_header.png)

Protein structure models like AlphaFold rely on Multiple Sequence Alignments (MSAs) for their prediction. Research has shown that the prediction of these models can be affected by manipulating the input MSAs, resulting in different conformations for the same target. To this end, we developed FrankenMSA, a small package designed to facilitate the workflow of manipulating MSAs. 

FrankenMSA offers a simple functional API to perform operations like:

- Filtering
- Slicing
- Cropping
- Clustering

Built to rely only on a Pandas Dataframe with a "sequence" column the package is designed for minimal requirements and maximal user freedom and compatibility with other scientific software. 

The current implementation inventory and migration tracker live in [docs/feature-index.md](docs/feature-index.md).

## Not a coder? - No problem!
<a href="https://colab.research.google.com/github/ibmm-unibe-ch/FrankenMSA/blob/dev/FrankenMSA_app_colab.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

We developed a **graphical user interface** using Dash to provide a clean and streamlined experience also to researchers who never wrote a line of code in their life. While the app naturally limits the functionality to some degree we worked hard to incorporate as much flexibility into it as possible. Are you missing something? Let us know! 

To launch the app just hit the "Open in Colab button above". A CPU runtime will suffice but depending on the size and number of MSAs you plan to use it may be worthwhile running the app on a a machine with more memory. (It works fine on an M-Series MacBook ✌️)

> Dash is known to have issues on Safari so it is recommended to use another browser like Chrome instead!

> To run the app locally clone this repository and run the `app/app.py` file via the terminal.

## Installation

We've provided a small helper script to set up a Python virtual environment and
install FrankenMSA in editable mode. From the repository root run:

```bash
./install.sh
```

This script will:

- create a virtual environment in `.venv`
- activate it and upgrade `pip`, `setuptools`, and `wheel`
- install the package in editable mode (`pip install -e .`) and attempt to
	install extras via `pip install -e .[all]` if available

Heavy optional tools such as ProteinMPNN are provisioned separately from
`scripts/installers/` rather than being auto-installed as part of the base
package. The library assumes those tools already exist and resolves them at
runtime via environment variables or the repository-local checkout.

To provision [ESM3](https://github.com/evolutionaryscale/esm) explicitly:

```bash
python scripts/installers/install_esm.py
```

To provision [GhostFold](https://github.com/brineylab/ghostfold) explicitly:

```bash
python scripts/installers/install_ghostfold.py
```

To provision [ProteinMPNN](https://github.com/dauparas/ProteinMPNN) explicitly:

```bash
python scripts/installers/install_proteinmpnn.py --root "$HOME/tools/ProteinMPNN"
```

The runtime resolver prefers these environment variables:

- `FRANKENMSA_PROTEINMPNN_ROOT`
- `PROTEINMPNN_LOCAL_ROOT`
- `ProteinMPNN_DIR`

GhostFold resolution prefers these environment variables before falling back to
the `ghostfold` executable on `PATH`:

- `FRANKENMSA_GHOSTFOLD_BIN`
- `GHOSTFOLD_BIN`
- `FRANKENMSA_GHOSTFOLD_ROOT`
- `GHOSTFOLD_ROOT`

Manual alternative (if you prefer to run commands yourself):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
# optionally: python -m pip install -e .[all]
```

After installation you can run the app locally with:

```bash
source .venv/bin/activate
python app/app.py
```

## Documentation

Sphinx documentation lives under `docs/` and includes API reference pages,
placeholders for GUI documentation, and a tutorial section prepared for
notebook-backed guides.

Install the documentation dependencies and build the site with:

```bash
python -m pip install -e .[docs]
sphinx-build -b html docs docs/_build/html
```

