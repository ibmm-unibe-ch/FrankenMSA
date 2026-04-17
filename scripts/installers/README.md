# Optional Dependency Installers

Heavy external tools are provisioned explicitly from this directory instead of being installed as part of the base FrankenMSA package.

Pattern:

- One installer entrypoint per special dependency.
- Each installer can be called directly by users, notebooks, or app helpers.
- Library code assumes the dependency is already available and only resolves paths.

Current installers:

- `install_proteinmpnn.py`: clones or refreshes a ProteinMPNN checkout, optionally installs lightweight Python helper dependencies, and ensures the default model weights are present.

Examples:

```bash
python scripts/installers/install_proteinmpnn.py --root /content/ProteinMPNN --install-python-deps
python scripts/installers/install_proteinmpnn.py --root "$HOME/tools/ProteinMPNN"
```

Runtime path resolution prefers these environment variables:

- `FRANKENMSA_PROTEINMPNN_ROOT`
- `PROTEINMPNN_LOCAL_ROOT`
- `ProteinMPNN_DIR`

Optional weight overrides:

- `FRANKENMSA_PROTEINMPNN_WEIGHTS_DIR`
- `FRANKENMSA_PROTEINMPNN_WEIGHTS_ROOT`
- `PROTEINMPNN_WEIGHTS_DIR`
- `PROTEINMPNN_WEIGHTS_ROOT`