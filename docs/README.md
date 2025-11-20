# MCPS Documentation

This directory contains the comprehensive Sphinx documentation for MCPS.

## Building the Documentation

### Prerequisites

Install documentation dependencies:

```bash
# From project root
uv sync --group docs
```

### Building HTML Documentation

```bash
cd docs
make html
```

The built documentation will be in `build/html/`. Open `build/html/index.html` in your browser.

### Other Formats

```bash
# PDF (requires LaTeX)
make latexpdf

# EPUB
make epub

# Plain text
make text

# Check for broken links
make linkcheck
```

### Clean Build

```bash
make clean
make html
```

## Documentation Structure

```
docs/
├── source/
│   ├── index.rst                # Main documentation index
│   ├── installation.rst         # Installation guide
│   ├── quick-start.rst          # Quick start guide
│   ├── architecture.rst         # System architecture
│   ├── data-dictionary.rst      # Database schema reference
│   ├── contributing.rst         # Contribution guidelines
│   ├── conf.py                  # Sphinx configuration
│   ├── _static/                 # Static assets (CSS, logos)
│   ├── _templates/              # Custom templates
│   ├── user-guide/              # User documentation
│   │   ├── index.rst
│   │   ├── cli-usage.rst
│   │   ├── dashboard.rst
│   │   └── data-exports.rst
│   ├── developer-guide/         # Developer documentation
│   │   ├── index.rst
│   │   ├── adding-adapters.rst
│   │   └── testing.rst
│   └── api/                     # API reference (auto-generated)
│       ├── index.rst
│       ├── harvester.rst
│       ├── adapters.rst
│       ├── analysis.rst
│       └── exporters.rst
├── build/                       # Built documentation (gitignored)
├── Makefile                     # Build commands (Unix)
├── make.bat                     # Build commands (Windows)
└── README.md                    # This file
```

## Sphinx Theme

We use the [Shibuya](https://shibuya.lepture.com/) theme with custom styling:

- **Accent Color:** Sky blue (#6a9fb5)
- **Dark Mode:** Fully supported
- **Search:** Built-in full-text search
- **Mobile:** Responsive design

## Auto-Generated API Documentation

The `api/` directory uses Sphinx autodoc to automatically generate documentation from Python docstrings.

To update API docs after code changes:

```bash
make clean
make html
```

## Writing Documentation

### reStructuredText Basics

Headings:
```rst
==========
Main Title
==========

Section
=======

Subsection
----------

Subsubsection
~~~~~~~~~~~~~
```

Code blocks:
```rst
.. code-block:: python

   def hello():
       print("Hello, world!")
```

Links:
```rst
:doc:`installation` - Link to another document
:ref:`section-label` - Link to a section
`External Link <https://example.com>`_
```

Admonitions:
```rst
.. note::
   This is a note

.. warning::
   This is a warning

.. tip::
   This is a tip
```

### MyST Markdown Support

You can also use Markdown files (`.md`) thanks to the MyST parser. They will be automatically converted to reStructuredText.

## Contributing to Documentation

1. Edit files in `docs/source/`
2. Build locally to preview changes: `make html`
3. Open `build/html/index.html` in your browser
4. Submit a pull request

### Style Guidelines

- Use **active voice** ("Run this command" not "This command can be run")
- Keep sentences short and clear
- Include code examples for all features
- Add cross-references between related pages
- Use consistent formatting for commands, file paths, etc.

## Deployment

Documentation is automatically built and deployed on:

- **GitHub Pages:** (configure in repository settings)
- **Read the Docs:** (connect repository)

## Troubleshooting

### Build Errors

**Problem:** `sphinx-build: command not found`

**Solution:**
```bash
uv sync --group docs
```

**Problem:** Module import errors in autodoc

**Solution:** Ensure the project is installed in editable mode:
```bash
uv pip install -e .
```

**Problem:** Theme not loading

**Solution:** Reinstall theme:
```bash
uv pip install --force-reinstall shibuya
```

### Common Issues

**Broken cross-references:**
Check that the target document or section exists and the reference syntax is correct.

**Missing API documentation:**
Ensure Python modules have proper docstrings in Google style.

**Build warnings:**
Run `make clean && make html` to clear cached builds.

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [Shibuya Theme Docs](https://shibuya.lepture.com/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [MyST Parser Guide](https://myst-parser.readthedocs.io/)

## License

Documentation is licensed under CC BY 4.0. Code examples are MIT licensed.
