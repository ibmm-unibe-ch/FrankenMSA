#!/usr/bin/env bash
set -euo pipefail

# Simple installer for FrankenMSA
# Creates a virtual environment and installs the package in editable mode.

VENV_DIR=".venv"

if [ -d "$VENV_DIR" ]; then
  echo "Virtual environment $VENV_DIR already exists. Skipping venv creation."
else
  echo "Creating virtual environment in $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Upgrading pip, setuptools, wheel..."
python -m pip install --upgrade pip setuptools wheel

echo "Installing FrankenMSA (editable)..."
# Try installing extras if available; fall back to plain editable install
if python -m pip install -e .[all]; then
  echo "Installed with extras."
else
  echo "Installing without extras..."
  python -m pip install -e .
fi

echo "Installation complete. To start using FrankenMSA run:"
echo "  source $VENV_DIR/bin/activate"
echo "To run the app locally: python app/app.py"
echo "Optional heavyweight tools are installed separately from scripts/installers/."
echo "Example: python scripts/installers/install_proteinmpnn.py --root \"$HOME/tools/ProteinMPNN\""
