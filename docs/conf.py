"""Sphinx configuration for the FrankenMSA documentation."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "FrankenMSA"
author = "Noah Kleinschmidt, Jannik Gut, Thommas Lemmin"
copyright = "2026, Noah Kleinschmidt, Jannik Gut, Thommas Lemmin"
release = "0.1.3"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
    "nbsphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_mock_imports = [
    "afcluster",
    "Bio",
    "dash",
    "dash_bio",
    "dash_bootstrap_components",
    "git",
    "httpx",
    "matplotlib",
    "plotly",
    "pybiolib",
    "pymsaviz",
    "requests",
    "scipy",
    "sklearn",
]

napoleon_google_docstring = False
napoleon_numpy_docstring = True

myst_enable_extensions = ["colon_fence"]

nbsphinx_execute = "never"

html_theme = "sphinx_rtd_theme"
html_title = "FrankenMSA documentation"
html_static_path = []