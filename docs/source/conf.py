# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "packages"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "MCPS"
project_full = "Model Context Protocol System"
author = "Wyatt Walsh"
copyright = f"2025, {author}"
release = "2.5.0"
version = "2.5.0"

# GitHub organization and repository
github_user = "wyattowalsh"
github_repo = "mcps"
github_url = f"https://github.com/{github_user}/{github_repo}"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # Core Sphinx extensions
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.githubpages",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",

    # MyST Parser - Markdown support
    "myst_parser",

    # Advanced autodoc
    "autodoc2",
    "autoclasstoc",
    "sphinx_autodoc_typehints",

    # Design and UI extensions
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx_tabs.tabs",
    "sphinx_togglebutton",
    "sphinxemoji.sphinxemoji",

    # Diagrams and visualization
    "sphinxcontrib.mermaid",

    # Domain-specific extensions
    "sphinx_click",
    "sphinx_jsonschema",
    "sphinxcontrib.httpdomain",

    # Git integration
    "sphinx_git",

    # Enhanced navigation
    "hoverxref.extension",
    "sphinx_sitemap",
    "notfound.extension",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**.ipynb_checkpoints",
    ".venv",
    "venv",
]

# Source suffix and master doc
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
master_doc = "index"

# Language and locale
language = "en"
locale_dirs = ["locales/"]
gettext_compact = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "shibuya"
html_static_path = ["_static"]
html_title = f"{project} Documentation"
html_short_title = project
html_baseurl = f"https://{github_user}.github.io/{github_repo}/"

# Shibuya theme options
html_theme_options = {
    "accent_color": "#6a9fb5",
    "github_url": github_url,
    "nav_links": [
        {
            "title": "Home",
            "url": "index",
        },
        {
            "title": "Installation",
            "url": "installation",
        },
        {
            "title": "Quick Start",
            "url": "quick-start",
        },
        {
            "title": "Guides",
            "url": "guides/index",
        },
        {
            "title": "API Reference",
            "url": "api/index",
        },
        {
            "title": "Changelog",
            "url": "changelog",
        },
    ],
    "dark_code": True,
    "light_logo": "_static/img/logo.svg",
    "dark_logo": "_static/img/logo.svg",
    "globaltoc_expand_depth": 2,
    "page_layout": "compact",
    "color_mode": "auto",
    "announcement": None,
    "twitter_url": None,
    "discord_url": None,
    "youtube_url": None,
    "twitter_site": None,
    "twitter_creator": None,
    "og_image_url": None,
    "carbon_ads_code": None,
    "carbon_ads_placement": None,
}

# HTML options
html_favicon = "_static/img/favicon/favicon.ico"
html_logo = "_static/img/logo.svg"
html_last_updated_fmt = "%b %d, %Y"
html_show_sphinx = False
html_show_copyright = True
html_copy_source = False
html_show_sourcelink = False

# Custom CSS and JS files
html_css_files = [
    "css/design-tokens.css",
    "css/custom.css",
    "css/components.css",
]

html_js_files = []

# -- Extension configuration -------------------------------------------------

# Napoleon settings (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
autodoc_class_signature = "separated"
autodoc_member_order = "bysource"
autodoc_mock_imports = []

# Autodoc2 settings (import-free API documentation)
autodoc2_packages = [
    {
        "path": "../../packages/harvester",
        "exclude_files": ["__pycache__", "tests"],
    },
]
autodoc2_render_plugin = "myst"
autodoc2_output_dir = "api/generated"
autodoc2_index_template = None
autodoc2_docstring_parser_regexes = [
    (r".*", "myst"),
]

# Autosummary settings
autosummary_generate = True
autosummary_imported_members = False

# Autoclasstoc settings
autoclasstoc_sections = [
    "public-attrs",
    "public-methods",
    "private-attrs",
    "private-methods",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
    "httpx": ("https://www.python-httpx.org/", None),
    "fastapi": ("https://fastapi.tiangolo.com/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "typer": ("https://typer.tiangolo.com/", None),
    "pytest": ("https://docs.pytest.org/en/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_timeout = 30

# MyST Parser settings
myst_enable_extensions = [
    "amsmath",
    "attrs_inline",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
    "attrs_block",
]
myst_heading_anchors = 3
myst_footnote_transition = True
myst_dmath_double_inline = True
myst_enable_checkboxes = True
myst_all_links_external = False
myst_url_schemes = {
    "http": None,
    "https": None,
    "ftp": None,
    "mailto": None,
    "gh": "https://github.com/{{path}}",
}

# MyST substitutions
myst_substitutions = {
    "project": project,
    "version": version,
    "release": release,
    "author": author,
    "github_url": github_url,
}

# Copy button settings
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"
copybutton_here_doc_delimiter = "EOT"
copybutton_selector = "div.highlight pre"

# Sphinx tabs settings
sphinx_tabs_disable_tab_closing = False
sphinx_tabs_valid_builders = ["html", "linkcheck"]

# Mermaid settings
mermaid_version = "10.6.1"
mermaid_init_js = """
mermaid.initialize({
    startOnLoad: true,
    theme: 'base',
    themeVariables: {
        primaryColor: '#6a9fb5',
        primaryTextColor: '#fff',
        primaryBorderColor: '#4a7f95',
        lineColor: '#4a7f95',
        secondaryColor: '#f0f4f8',
        tertiaryColor: '#e2e8f0',
        background: '#ffffff',
        mainBkg: '#6a9fb5',
        secondBkg: '#f0f4f8',
        mainContrastColor: '#ffffff',
        darkMode: false,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        fontSize: '16px',
    },
    flowchart: {
        htmlLabels: true,
        curve: 'basis',
        useMaxWidth: true,
    },
    sequence: {
        diagramMarginX: 50,
        diagramMarginY: 10,
        actorMargin: 50,
        width: 150,
        height: 65,
        boxMargin: 10,
        boxTextMargin: 5,
        noteMargin: 10,
        messageMargin: 35,
        mirrorActors: true,
        bottomMarginAdj: 1,
        useMaxWidth: true,
    },
    gantt: {
        titleTopMargin: 25,
        barHeight: 20,
        barGap: 4,
        topPadding: 50,
        leftPadding: 75,
        gridLineStartPadding: 35,
        fontSize: 11,
        numberSectionStyles: 4,
        axisFormat: '%Y-%m-%d',
    },
});
"""
mermaid_d3_zoom = True
mermaid_output_format = "svg"

# Todo extension settings
todo_include_todos = True
todo_emit_warnings = False
todo_link_only = False

# Sphinx-git settings
sphinx_git_track_branches = ["main", "master"]

# HoverXRef settings
hoverxref_auto_ref = True
hoverxref_domains = ["py"]
hoverxref_roles = [
    "option",
    "doc",
    "term",
]
hoverxref_role_types = {
    "ref": "modal",
    "confval": "tooltip",
    "mod": "tooltip",
    "class": "tooltip",
}
hoverxref_mathjax = True

# Sitemap settings
html_extra_path = []
sitemap_url_scheme = "{link}"
sitemap_filename = "sitemap.xml"
sitemap_locales = [None]

# notfound settings
notfound_context = {
    "title": "Page Not Found",
    "body": """
<h1>Page Not Found</h1>
<p>Sorry, we couldn't find that page.</p>
<p>Try using the search box or go back to the <a href="/">homepage</a>.</p>
""",
}
notfound_urls_prefix = "/"

# External links
extlinks = {
    "issue": (f"{github_url}/issues/%s", "#%s"),
    "pr": (f"{github_url}/pull/%s", "PR #%s"),
    "commit": (f"{github_url}/commit/%s", "%s"),
    "gh": ("https://github.com/%s", "GitHub: %s"),
    "pypi": ("https://pypi.org/project/%s/", "PyPI: %s"),
    "npm": ("https://www.npmjs.com/package/%s", "NPM: %s"),
}

# Typehints settings
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True
typehints_use_rtype = True
typehints_defaults = "comma"
simplify_optional_unions = True

# Coverage settings (for sphinx.ext.coverage)
coverage_show_missing_items = True
coverage_ignore_modules = []
coverage_ignore_functions = []
coverage_ignore_classes = []
coverage_write_headline = False

# Emoji support
sphinxemoji_style = "twemoji"

# HTTP domain settings
http_headers_ignore_prefixes = ["X-"]
http_strict_mode = False

# Nitpicky mode - warn about all missing references
nitpicky = False
nitpick_ignore = [
    ("py:class", "type"),
    ("py:class", "optional"),
]

# Smart quotes
smartquotes = True
smartquotes_action = "qDe"
smartquotes_excludes = {
    "languages": ["ja"],
    "builders": ["man", "text"],
}
