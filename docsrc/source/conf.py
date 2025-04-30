# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'autorino'
copyright = '2025 - Pierre Sakic'
author = 'Pierre Sakic'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",       # Auto-generate docs from Python
    "sphinx.ext.napoleon",      # Google/Numpy-style docstrings
    "sphinx.ext.viewcode",      # Add links to source code
    "sphinx.ext.intersphinx",   # Link to other projects' docs
    "myst_parser",              # Markdown support (optional)
    "sphinx_rtd_dark_mode",
    'sphinxarg.ext',
    'sphinxcontrib.programoutput'
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']
# user starts in dark mode
default_dark_mode = True


# Enable autodoc to scan your Python code
import os
import sys
sys.path.insert(0, os.path.abspath("../.."))  # Adjust path to your project root

# Napoleon settings (for docstrings)
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True

html_logo = "logo_autorino.png"
html_theme_options = {
    'logo_only': True,
    'display_version': False,
}
