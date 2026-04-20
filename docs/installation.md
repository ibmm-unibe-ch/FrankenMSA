# Installation

FrankenMSA can be installed in editable mode from the repository root.

## Library install

```bash
./install.sh
```

Manual setup remains available if you prefer to manage the environment yourself:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

## Documentation dependencies

Install the documentation extras before building the Sphinx site:

```bash
python -m pip install -e .[docs]
```

## Build the documentation

From the repository root:

```bash
sphinx-build -b html docs docs/_build/html
```

The generated site will be written to `docs/_build/html`.