"""Sphinx configuration for the hexacore documentation."""

from __future__ import annotations

import os
import sys
from importlib import metadata

# Make the source package importable for any tooling that needs it.
# (sphinx-autoapi performs static analysis so this is not strictly required,
# but it helps intersphinx and viewcode.)
sys.path.insert(0, os.path.abspath("../../src"))


# -- Project information -----------------------------------------------------

project = "hexacore"
author = "Kamal Farahani"
copyright = "2026, Kamal Farahani"

try:
    release = metadata.version("hexacore")
except metadata.PackageNotFoundError:  # pragma: no cover - docs build fallback
    release = "0.1.0"
version = ".".join(release.split(".")[:2])


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "autoapi.extension",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

# -- Napoleon (Google-style docstrings) --------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# -- AutoAPI -----------------------------------------------------------------

autoapi_type = "python"
autoapi_dirs = ["../../src/hexacore"]
autoapi_root = "api"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "special-members",
]
autoapi_python_class_content = "both"
autoapi_member_order = "groupwise"
autoapi_keep_files = False
autoapi_add_toctree_entry = False  # we add it manually from index.rst

# -- Intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

# -- HTML output -------------------------------------------------------------

html_theme = "furo"
html_title = "hexacore"
html_static_path = ["_static"]

# -- sphinx-copybutton -------------------------------------------------------

copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True

# -- Nitpick / cross-reference suppression -----------------------------------

# Generic TypeVars used throughout the codebase that don't resolve as classes.
nitpick_ignore = [
    ("py:class", "M"),
    ("py:obj", "M"),
]

# Suppress noisy cross-reference warnings that come from AutoAPI emitting
# the same symbol under multiple dotted paths.
suppress_warnings = [
    "ref.python",
]
