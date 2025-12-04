# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------

project = 'FEDI'
copyright = '2024, Snoussi'
author = 'Haykel Snoussi'
release = '1.0.1'
version = '1.0.1'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    'display_version': True,
    'navigation_depth': 3,
    'collapse_navigation': False,
    'style_external_links': True,
    # 'logo_only': False, # this should be commented to have "FEDI" written in top left corner.
    'prev_next_buttons_location': 'bottom',
    'style_nav_header_background': '#2980B9',

    # GitHub buttons
    'display_github': True,
    'github_user': 'FEDIToolbox',
    'github_repo': 'FEDI',
    'github_version': 'main',
    'conf_py_path': '/documentation/source/',
}

# Logo and favicon
html_logo = "FEDI"
# html_logo = '_static/Focus_FEDI.png'
# html_favicon = '_static/favicon.ico'  # Add this if you have one
html_static_path = ['_static']

# -- Options for EPUB output -------------------------------------------------

epub_show_urls = 'footnote'

# -- LaTeX / PDF Output ------------------------------------------------------

latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
    'figure_align': 'H',
}
