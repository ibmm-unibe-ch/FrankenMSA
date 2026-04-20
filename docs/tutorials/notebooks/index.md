# Notebook Tutorial Hub

Notebook-backed tutorials will live here.

## Planned structure

- one page per tutorial notebook
- lightweight narrative pages around longer notebooks when needed
- shared conventions for inputs, expected runtime, and outputs

## How to add a notebook later

1. Place the notebook under `docs/tutorials/notebooks/`.
2. Add it to the local toctree on this page.
3. Rebuild the site with `sphinx-build -b html docs docs/_build/html`.

The documentation is already configured not to execute notebooks during the
build, which keeps tutorial rendering stable and predictable.