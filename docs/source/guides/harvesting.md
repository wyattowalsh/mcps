---
title: Harvesting Guide
description: Complete guide to harvesting MCP servers from various sources
---

# Harvesting Guide

Learn how to harvest MCP servers from various sources using MCPS.

## Supported Sources

::::{grid} 1 1 2 3
:gutter: 2

:::{grid-item-card} {octicon}`mark-github` GitHub
:class-header: bg-primary text-white
GraphQL API with in-memory file parsing
:::

:::{grid-item-card} {octicon}`package` NPM
:class-header: bg-danger text-white
Registry API with tarball inspection
:::

:::{grid-item-card} {octicon}`package` PyPI
:class-header: bg-info text-white
JSON API with wheel/sdist analysis
:::

::::

## GitHub Harvesting

### Basic Usage

```bash
uv run python -m packages.harvester.cli ingest \
  --strategy github \
  --target https://github.com/modelcontextprotocol/servers
```

### Authentication

```{admonition} GitHub Token Required
:class: important
Set `GITHUB_TOKEN` in `.env` for higher rate limits (5,000 req/hour vs 60).
```

### What Gets Harvested

- Repository metadata (stars, forks, description)
- MCP configuration from `mcp.json`
- Package manifests (`package.json`, `pyproject.toml`)
- README content for RAG workflows
- Contributor information
- Release history

## NPM Harvesting

```bash
uv run python -m packages.harvester.cli ingest \
  --strategy npm \
  --target @modelcontextprotocol/server-filesystem
```

### Package Inspection

MCPS downloads and inspects NPM tarballs to extract:
- MCP server configurations
- Tool definitions
- Dependencies
- Security patterns

```{note}
Tarballs are processed in-memory with zip bomb protection (max 500MB uncompressed).
```

## PyPI Harvesting

```bash
uv run python -m packages.harvester.cli ingest \
  --strategy pypi \
  --target mcp-server-git
```

### Detection Heuristics

Since PyPI lacks standardized MCP config:
- Scans `pyproject.toml` for MCP metadata
- Detects `@mcp.tool` decorators
- Analyzes entry points

## Batch Harvesting

### From File

```bash
# Create urls.txt with one URL per line
cat urls.txt | while read url; do
  uv run python -m packages.harvester.cli ingest --strategy auto --target "$url"
done
```

### Error Handling

MCPS includes automatic retry logic:
- Exponential backoff (2-30 seconds)
- 5 retry attempts
- Checkpoint system for recovery

## See Also

- [CLI Usage](../user-guide/cli-usage.md)
- [Architecture](../architecture.md)
- [API Reference](../api/harvester.md)
