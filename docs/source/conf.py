"""
Sphinx configuration for MCPS Dev Docs.

This is a comprehensive, production-grade documentation configuration
adapted from the Frame Python example with MCPS-specific customizations.
"""

# =============================================================================
# Standard Library Imports
# =============================================================================

import os
import sys
from pathlib import Path
from datetime import datetime

# =============================================================================
# Path Configuration
# =============================================================================

# Define key repository paths for easy reference
DOCS_ROOT = Path(__file__).parent.parent  # docs/
REPO_ROOT = DOCS_ROOT.parent  # /home/user/mcps/
PKG_ROOT = REPO_ROOT / "packages"  # packages/ (harvester, shared)
APP_ROOT = REPO_ROOT / "apps"  # apps/ (web, api)

# Make packages and apps importable for autodoc and autodoc2
# This allows Sphinx to import and document Python modules
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(PKG_ROOT))
sys.path.insert(0, str(APP_ROOT))

# Add specific package paths for better module resolution
sys.path.insert(0, str(PKG_ROOT / "harvester"))
sys.path.insert(0, str(APP_ROOT / "api"))

# =============================================================================
# Project Information
# =============================================================================
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "MCPS Dev Docs"
project_full = "Model Context Protocol System - Developer Documentation"
project_short = "MCPS"
author = "Wyatt Walsh"
copyright = f"2025, {author}"
release = "2.5.0"
version = "2.5.0"

# GitHub organization and repository information
github_user = "wyattowalsh"
github_repo = "mcps"
github_url = f"https://github.com/{github_user}/{github_repo}"

# =============================================================================
# General Configuration
# =============================================================================
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # -------------------------------------------------------------------------
    # Core Sphinx Extensions
    # -------------------------------------------------------------------------
    "sphinx.ext.autodoc",           # Extract docstrings from Python code
    "sphinx.ext.autosummary",       # Generate summary tables for modules
    "sphinx.ext.napoleon",          # Support Google/NumPy style docstrings
    "sphinx.ext.viewcode",          # Add links to highlighted source code
    "sphinx.ext.intersphinx",       # Link to other projects' documentation
    "sphinx.ext.todo",              # Support for TODO items in docs
    "sphinx.ext.coverage",          # Documentation coverage statistics
    "sphinx.ext.extlinks",          # Shorten external links
    "sphinx.ext.githubpages",       # Publish HTML docs via GitHub Pages
    "sphinx.ext.ifconfig",          # Conditional content based on config

    # -------------------------------------------------------------------------
    # MyST Parser - Enhanced Markdown Support
    # -------------------------------------------------------------------------
    "myst_parser",                  # Parse Markdown files with extended syntax

    # -------------------------------------------------------------------------
    # Advanced API Documentation
    # -------------------------------------------------------------------------
    "autodoc2",                     # Import-free API documentation from AST
    "sphinx_autodoc_typehints",     # Better type hints in documentation
    "autoclasstoc",                 # Auto-generate class table of contents

    # -------------------------------------------------------------------------
    # UX and Design Extensions
    # -------------------------------------------------------------------------
    "sphinx_design",                # Material Design components (cards, grids, etc.)
    "sphinx_copybutton",            # Add copy button to code blocks
    "sphinx_tabs.tabs",             # Tabbed content support
    "sphinx_togglebutton",          # Collapsible content buttons
    "sphinxemoji.sphinxemoji",      # Emoji support in docs

    # -------------------------------------------------------------------------
    # Diagram and Visualization
    # -------------------------------------------------------------------------
    "sphinxcontrib.mermaid",        # Mermaid diagram support

    # -------------------------------------------------------------------------
    # CLI and API Documentation
    # -------------------------------------------------------------------------
    "sphinx_click",                 # Document Click CLI applications
    "sphinx_jsonschema",            # Render JSON schemas
    "sphinxcontrib.httpdomain",     # HTTP API documentation

    # -------------------------------------------------------------------------
    # Git Integration
    # -------------------------------------------------------------------------
    "sphinx_git",                   # Git changelog and metadata

    # -------------------------------------------------------------------------
    # Enhanced Navigation and Metadata
    # -------------------------------------------------------------------------
    "hoverxref.extension",          # Show tooltips on hover for references
    "sphinx_sitemap",               # Generate sitemap.xml for SEO
    "notfound.extension",           # Custom 404 page
]

# Template and static file paths
templates_path = ["_templates"]
html_static_path = ["_static"]

# Patterns to exclude when looking for source files
exclude_patterns = [
    "_build",
    "_templates",
    "Thumbs.db",
    ".DS_Store",
    "**.ipynb_checkpoints",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "*.egg-info",
]

# Source file suffixes and master document
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
master_doc = "index"

# Language and internationalization
language = "en"
locale_dirs = ["locales/"]
gettext_compact = False

# =============================================================================
# HTML Output Configuration
# =============================================================================
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "shibuya"
html_title = f"{project} v{version}"
html_short_title = project_short
html_baseurl = f"https://{github_user}.github.io/{github_repo}/"

# -------------------------------------------------------------------------
# Shibuya Theme Options
# -------------------------------------------------------------------------
# https://shibuya.lepture.com/customisation/

html_theme_options = {
    # Brand color - MCPS teal
    "accent_color": "#6a9fb5",

    # GitHub repository link
    "github_url": github_url,

    # Navigation links
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
            "title": "Tools",
            "url": "tools/index",
        },
        {
            "title": "Reference",
            "url": "api/index",
        },
        {
            "title": "Changelog",
            "url": "changelog",
        },
    ],

    # Code block styling
    "dark_code": True,

    # Logo configuration (light and dark mode)
    "light_logo": "_static/img/logo.svg",
    "dark_logo": "_static/img/logo.svg",

    # Global table of contents settings
    "globaltoc_expand_depth": 2,  # Auto-expand 2 levels

    # Page layout
    "page_layout": "compact",

    # Color mode (auto, light, dark)
    "color_mode": "auto",

    # Optional social/announcement links
    "announcement": None,
    "twitter_url": None,
    "discord_url": None,
    "youtube_url": None,
    "twitter_site": None,
    "twitter_creator": None,
    "og_image_url": None,

    # Carbon ads (if applicable)
    "carbon_ads_code": None,
    "carbon_ads_placement": None,
}

# HTML branding and metadata
html_favicon = "_static/img/favicon/favicon.ico"
html_logo = "_static/img/logo.svg"
html_last_updated_fmt = "%b %d, %Y"
html_show_sphinx = False
html_show_copyright = True
html_copy_source = False
html_show_sourcelink = False

# Custom CSS and JavaScript files
html_css_files = [
    "css/design-tokens.css",
    "css/custom.css",
    "css/components.css",
]

html_js_files = []

# Extra paths for static files (sitemap, robots.txt, etc.)
html_extra_path = []

# =============================================================================
# Extension Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# Napoleon - Google/NumPy Style Docstrings
# -----------------------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html

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

# -----------------------------------------------------------------------------
# Autodoc - Extract Documentation from Python Docstrings
# -----------------------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

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

# Suppress warnings for common issues
autodoc_warningiserror = False

# -----------------------------------------------------------------------------
# Autodoc2 - Import-Free API Documentation
# -----------------------------------------------------------------------------
# https://sphinx-autodoc2.readthedocs.io/

# Scan all Python packages and apps
autodoc2_packages = []

# Add packages from packages/ directory
for pkg_dir in PKG_ROOT.iterdir():
    if pkg_dir.is_dir() and not pkg_dir.name.startswith((".", "_")):
        pkg_path = pkg_dir.relative_to(REPO_ROOT)
        autodoc2_packages.append({
            "path": f"../../{pkg_path}",
            "exclude_files": [
                "__pycache__",
                "tests",
                "test_*.py",
                "*_test.py",
                "conftest.py",
                ".pytest_cache",
                "build",
                "dist",
                "*.egg-info",
            ],
        })
        print(f"[autodoc2] Scanning package: {pkg_path}")

# Add apps from apps/ directory
for app_dir in APP_ROOT.iterdir():
    if app_dir.is_dir() and not app_dir.name.startswith((".", "_")):
        app_path = app_dir.relative_to(REPO_ROOT)
        autodoc2_packages.append({
            "path": f"../../{app_path}",
            "exclude_files": [
                "__pycache__",
                "tests",
                "test_*.py",
                "*_test.py",
                "conftest.py",
                ".pytest_cache",
                "build",
                "dist",
                "*.egg-info",
                "node_modules",
                ".next",
                "public",
                "static",
            ],
        })
        print(f"[autodoc2] Scanning app: {app_path}")

# Print summary
print(f"[autodoc2] Total packages/apps to scan: {len(autodoc2_packages)}")

# Autodoc2 rendering settings
autodoc2_render_plugin = "myst"
autodoc2_output_dir = "api/generated"
autodoc2_index_template = None
autodoc2_docstring_parser_regexes = [
    (r".*", "myst"),  # Parse all docstrings as MyST
]

# Additional autodoc2 options
autodoc2_module_all_regexes = [
    r".*",  # Document all modules
]
autodoc2_hidden_objects = ["private", "dunder"]  # Hide private and dunder methods

# -----------------------------------------------------------------------------
# Autosummary - Generate Summary Tables
# -----------------------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html

autosummary_generate = True
autosummary_imported_members = False
autosummary_ignore_module_all = False

# -----------------------------------------------------------------------------
# Autoclasstoc - Auto-Generate Class ToC
# -----------------------------------------------------------------------------
# https://autoclasstoc.readthedocs.io/

autoclasstoc_sections = [
    "public-attrs",
    "public-methods",
    "private-attrs",
    "private-methods",
]

# -----------------------------------------------------------------------------
# Intersphinx - Link to Other Documentation
# -----------------------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html

intersphinx_mapping = {
    # Python ecosystem
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),

    # Scientific Python
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),

    # CLI frameworks
    "click": ("https://click.palletsprojects.com/", None),
    "typer": ("https://typer.tiangolo.com/", None),

    # Web frameworks
    "fastapi": ("https://fastapi.tiangolo.com/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "uvicorn": ("https://www.uvicorn.org/", None),
    "starlette": ("https://www.starlette.io/", None),

    # Database and ORM
    "sqlalchemy": ("https://docs.sqlalchemy.org/en/20/", None),
    "alembic": ("https://alembic.sqlalchemy.org/en/latest/", None),

    # HTTP clients
    "httpx": ("https://www.python-httpx.org/", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),

    # Testing
    "pytest": ("https://docs.pytest.org/en/stable/", None),

    # Async
    "anyio": ("https://anyio.readthedocs.io/en/stable/", None),
    "trio": ("https://trio.readthedocs.io/en/stable/", None),
}
intersphinx_timeout = 30
intersphinx_cache_limit = 7  # Days

# -----------------------------------------------------------------------------
# MyST Parser - Markdown with Extended Syntax
# -----------------------------------------------------------------------------
# https://myst-parser.readthedocs.io/

# Enable all 14 MyST extensions
myst_enable_extensions = [
    "amsmath",          # LaTeX math via amsmath
    "attrs_block",      # Block-level attributes
    "attrs_inline",     # Inline attributes
    "colon_fence",      # ::: code fences
    "deflist",          # Definition lists
    "dollarmath",       # $...$ and $$...$$ math
    "fieldlist",        # Field lists
    "html_admonition",  # HTML-based admonitions
    "html_image",       # HTML image syntax
    "linkify",          # Auto-detect URLs
    "replacements",     # Text replacements
    "smartquotes",      # Smart quotes
    "strikethrough",    # ~~strikethrough~~
    "substitution",     # Variable substitutions
    "tasklist",         # GitHub-style task lists
]

# MyST configuration options
myst_heading_anchors = 3              # Auto-generate anchors for h1-h3
myst_footnote_transition = True       # Add horizontal rule before footnotes
myst_dmath_double_inline = True       # Allow $$ for inline math
myst_enable_checkboxes = True         # Enable checkbox rendering
myst_all_links_external = False       # Don't treat all links as external
myst_url_schemes = {
    "http": None,
    "https": None,
    "ftp": None,
    "mailto": None,
    "gh": "https://github.com/{{path}}",
}

# MyST substitutions (variables usable in Markdown)
myst_substitutions = {
    "project": project,
    "project_full": project_full,
    "project_short": project_short,
    "version": version,
    "release": release,
    "author": author,
    "github_url": github_url,
    "github_user": github_user,
    "github_repo": github_repo,
}

# -----------------------------------------------------------------------------
# Sphinx Copybutton - Add Copy Button to Code Blocks
# -----------------------------------------------------------------------------
# https://sphinx-copybutton.readthedocs.io/

copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"
copybutton_here_doc_delimiter = "EOT"
copybutton_selector = "div.highlight pre"
copybutton_remove_prompts = True

# -----------------------------------------------------------------------------
# Sphinx Tabs - Tabbed Content
# -----------------------------------------------------------------------------
# https://sphinx-tabs.readthedocs.io/

sphinx_tabs_disable_tab_closing = False
sphinx_tabs_valid_builders = ["html", "linkcheck"]

# -----------------------------------------------------------------------------
# Mermaid - Diagram Support with Comprehensive Theme Configuration
# -----------------------------------------------------------------------------
# https://sphinxcontrib-mermaid-demo.readthedocs.io/

mermaid_version = "10.6.1"

# Comprehensive Mermaid configuration with MCPS branding
mermaid_init_js = """
mermaid.initialize({
    startOnLoad: true,
    theme: 'base',
    themeVariables: {
        // Primary MCPS teal color scheme
        primaryColor: '#6a9fb5',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#4a7f95',

        // Secondary colors
        secondaryColor: '#f0f4f8',
        secondaryTextColor: '#1a202c',
        secondaryBorderColor: '#cbd5e0',

        // Tertiary colors
        tertiaryColor: '#e2e8f0',
        tertiaryTextColor: '#2d3748',
        tertiaryBorderColor: '#a0aec0',

        // Background and contrast
        background: '#ffffff',
        mainBkg: '#6a9fb5',
        secondBkg: '#f0f4f8',
        mainContrastColor: '#ffffff',

        // Line and edge colors
        lineColor: '#4a7f95',
        edgeLabelBackground: '#ffffff',

        // Additional theme variables
        clusterBkg: '#f7fafc',
        clusterBorder: '#cbd5e0',
        defaultLinkColor: '#4a7f95',
        titleColor: '#1a202c',

        // Font configuration
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        fontSize: '16px',

        // Node styling
        nodeBorder: '#4a7f95',
        nodeTextColor: '#1a202c',

        // Dark mode indicator (overridden by themeCSS)
        darkMode: false,
    },

    // Custom CSS for dark mode support
    themeCSS: `
        /* Light mode (default) */
        .node rect,
        .node circle,
        .node polygon {
            fill: #6a9fb5 !important;
            stroke: #4a7f95 !important;
        }

        .edgeLabel {
            background-color: #ffffff !important;
            color: #1a202c !important;
        }

        /* Dark mode overrides */
        html.dark .node rect,
        html.dark .node circle,
        html.dark .node polygon {
            fill: #5a8fa5 !important;
            stroke: #6a9fb5 !important;
        }

        html.dark .edgeLabel {
            background-color: #2d3748 !important;
            color: #e2e8f0 !important;
        }

        html.dark .label {
            color: #e2e8f0 !important;
        }

        html.dark .cluster rect {
            fill: #1a202c !important;
            stroke: #4a5568 !important;
        }
    `,

    // Flowchart configuration
    flowchart: {
        htmlLabels: true,
        curve: 'basis',
        useMaxWidth: true,
        diagramPadding: 8,
        nodeSpacing: 50,
        rankSpacing: 50,
        padding: 15,
    },

    // Sequence diagram configuration
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
        rightAngles: false,
        showSequenceNumbers: false,
    },

    // Gantt chart configuration
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
        useMaxWidth: true,
    },

    // Class diagram configuration
    class: {
        useMaxWidth: true,
        defaultRenderer: 'dagre-wrapper',
    },

    // State diagram configuration
    state: {
        dividerMargin: 10,
        sizeUnit: 5,
        padding: 8,
        textHeight: 10,
        titleShift: -15,
        noteMargin: 10,
        forkWidth: 70,
        forkHeight: 7,
        miniPadding: 2,
        fontSizeFactor: 5.02,
        fontSize: 24,
        labelHeight: 16,
        edgeLengthFactor: '20',
        compositeTitleSize: 35,
        radius: 5,
        useMaxWidth: true,
    },

    // ER diagram configuration
    er: {
        diagramPadding: 20,
        layoutDirection: 'TB',
        minEntityWidth: 100,
        minEntityHeight: 75,
        entityPadding: 15,
        stroke: 'gray',
        fill: 'honeydew',
        fontSize: 12,
        useMaxWidth: true,
    },

    // Journey diagram configuration
    journey: {
        diagramMarginX: 50,
        diagramMarginY: 10,
        actorMargin: 50,
        width: 150,
        height: 65,
        boxMargin: 10,
        boxTextMargin: 5,
        noteMargin: 10,
        messageMargin: 35,
        useMaxWidth: true,
    },

    // Pie chart configuration
    pie: {
        useMaxWidth: true,
    },

    // Git graph configuration
    gitGraph: {
        diagramPadding: 8,
        nodeLabel: {
            width: 75,
            height: 100,
            x: -25,
            y: 0,
        },
        mainBranchName: 'main',
        mainBranchOrder: 0,
        showCommitLabel: true,
        showBranches: true,
        rotateCommitLabel: true,
    },

    // Requirement diagram configuration
    requirement: {
        useMaxWidth: true,
    },

    // Security configuration
    secure: ['secure', 'securityLevel', 'startOnLoad', 'maxTextSize'],
    securityLevel: 'loose',
});
"""

# Mermaid output format and options
mermaid_d3_zoom = True
mermaid_output_format = "svg"

# -----------------------------------------------------------------------------
# Sphinx Autodoc Typehints
# -----------------------------------------------------------------------------
# https://github.com/tox-dev/sphinx-autodoc-typehints

typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True
typehints_use_rtype = True
typehints_defaults = "comma"
simplify_optional_unions = True
typehints_use_signature = False
typehints_use_signature_return = False

# -----------------------------------------------------------------------------
# Todo Extension
# -----------------------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html

todo_include_todos = True
todo_emit_warnings = False
todo_link_only = False

# -----------------------------------------------------------------------------
# Coverage Extension
# -----------------------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/coverage.html

coverage_show_missing_items = True
coverage_ignore_modules = []
coverage_ignore_functions = []
coverage_ignore_classes = []
coverage_write_headline = False

# -----------------------------------------------------------------------------
# Sphinx-Git - Git Integration
# -----------------------------------------------------------------------------
# https://sphinx-git.readthedocs.io/

sphinx_git_track_branches = ["main", "master"]

# -----------------------------------------------------------------------------
# HoverXRef - Hover Tooltips for References
# -----------------------------------------------------------------------------
# https://sphinx-hoverxref.readthedocs.io/

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
    "func": "tooltip",
    "meth": "tooltip",
    "attr": "tooltip",
    "exc": "tooltip",
    "data": "tooltip",
}
hoverxref_mathjax = True
hoverxref_tooltip_maxwidth = 600
hoverxref_modal_hover_delay = 500

# -----------------------------------------------------------------------------
# Sitemap - Generate sitemap.xml
# -----------------------------------------------------------------------------
# https://sphinx-sitemap.readthedocs.io/

sitemap_url_scheme = "{link}"
sitemap_filename = "sitemap.xml"
sitemap_locales = [None]

# -----------------------------------------------------------------------------
# Notfound - Custom 404 Page
# -----------------------------------------------------------------------------
# https://sphinx-notfound-page.readthedocs.io/

notfound_context = {
    "title": "Page Not Found",
    "body": """
<h1>Page Not Found</h1>
<p>Sorry, we couldn't find that page.</p>
<p>Try using the search box or go back to the <a href="/">homepage</a>.</p>
""",
}
notfound_urls_prefix = "/"
notfound_no_urls_prefix = False

# -----------------------------------------------------------------------------
# External Links - Shorten Common URLs
# -----------------------------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html

extlinks = {
    "issue": (f"{github_url}/issues/%s", "#%s"),
    "pr": (f"{github_url}/pull/%s", "PR #%s"),
    "commit": (f"{github_url}/commit/%s", "%s"),
    "gh": ("https://github.com/%s", "GitHub: %s"),
    "pypi": ("https://pypi.org/project/%s/", "PyPI: %s"),
    "npm": ("https://www.npmjs.com/package/%s", "NPM: %s"),
    "mcp": ("https://modelcontextprotocol.io/%s", "MCP: %s"),
}
extlinks_detect_hardcoded_links = True

# -----------------------------------------------------------------------------
# Emoji Support
# -----------------------------------------------------------------------------
# https://sphinxemoji.readthedocs.io/

sphinxemoji_style = "twemoji"

# -----------------------------------------------------------------------------
# HTTP Domain - REST API Documentation
# -----------------------------------------------------------------------------
# https://sphinxcontrib-httpdomain.readthedocs.io/

http_headers_ignore_prefixes = ["X-"]
http_strict_mode = False
http_index_ignore_prefixes = ["/api/v1"]

# -----------------------------------------------------------------------------
# Sphinx Click - CLI Documentation
# -----------------------------------------------------------------------------
# https://sphinx-click.readthedocs.io/

# No specific configuration needed - works out of the box

# -----------------------------------------------------------------------------
# JSON Schema - Schema Documentation
# -----------------------------------------------------------------------------
# https://sphinx-jsonschema.readthedocs.io/

# No specific configuration needed - works out of the box

# =============================================================================
# Additional Sphinx Settings
# =============================================================================

# Nitpicky mode - warn about all missing references
nitpicky = False
nitpick_ignore = [
    ("py:class", "type"),
    ("py:class", "optional"),
    ("py:class", "typing.Optional"),
    ("py:class", "typing.Any"),
]
nitpick_ignore_regex = [
    (r"py:.*", r".*\..*"),  # Ignore cross-references to submodules
]

# Smart quotes configuration
smartquotes = True
smartquotes_action = "qDe"
smartquotes_excludes = {
    "languages": ["ja"],
    "builders": ["man", "text"],
}

# Suppress warnings
suppress_warnings = [
    "myst.header",  # Suppress MyST header warnings
    "autodoc",      # Suppress autodoc warnings for missing modules
]

# Maximum depth for table of contents
toc_object_entries_show_parents = "hide"

# Numbering
numfig = True
numfig_secnum_depth = 2
numfig_format = {
    "figure": "Figure %s",
    "table": "Table %s",
    "code-block": "Listing %s",
    "section": "Section %s",
}

# Footnote settings
footnote_references = "superscript"

# Figure and image settings
figure_language_filename = "{root}.{language}{ext}"

# Highlight language
highlight_language = "python3"
highlight_options = {
    "stripnl": False,
}

# Pygments style
pygments_style = "sphinx"
pygments_dark_style = "monokai"

# Link check configuration
linkcheck_ignore = [
    r"http://localhost:\d+/?",  # Ignore localhost links
]
linkcheck_timeout = 15
linkcheck_workers = 5

# =============================================================================
# Print Configuration Summary
# =============================================================================

print("=" * 80)
print(f"MCPS Documentation Configuration")
print("=" * 80)
print(f"Project: {project}")
print(f"Version: {version}")
print(f"GitHub: {github_url}")
print(f"Theme: {html_theme}")
print(f"Extensions: {len(extensions)}")
print(f"Intersphinx: {len(intersphinx_mapping)} mappings")
print(f"MyST Extensions: {len(myst_enable_extensions)}")
print("=" * 80)
