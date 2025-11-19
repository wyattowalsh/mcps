---
title: Analysis Guide
description: Understanding MCPS security analysis and health scoring
---

# Analysis Guide

MCPS provides comprehensive analysis of MCP servers including security scanning, health scoring, and embedding generation.

## Security Analysis

### AST-Based Scanning

MCPS uses Abstract Syntax Tree (AST) analysis to detect dangerous patterns **without executing code**.

```{mermaid}
flowchart LR
    CODE[Source Code] --> PARSE[Parse AST]
    PARSE --> SCAN[Pattern Scanner]
    SCAN --> RISK[Risk Assessment]
    RISK --> DB[(Database)]
```

### Detection Categories

| Category | Python Patterns | JS/TS Patterns |
|----------|----------------|----------------|
| Code Execution | `eval()`, `exec()`, `compile()` | `eval()` |
| Subprocess | `subprocess.run()`, `os.system()` | `child_process.exec()`, `spawn()` |
| Network | `socket`, `requests`, `httpx` | `fetch()`, `http`, `net` |
| Filesystem | `os`, `shutil`, `pathlib` | `fs.writeFile()`, `fs-extra` |

### Risk Levels

:::::{grid} 1 1 2 2
:gutter: 2

::::{grid-item-card} {bdg-success}`Safe`
Verified and sandboxed. Official repos with no dangerous operations.
::::

::::{grid-item-card} {bdg-warning}`Moderate`
Network or read-only FS. Uses network/filesystem but verified.
::::

::::{grid-item-card} {bdg-danger}`High`
Unverified with dangerous ops. Shell execution, write access, subprocess.
::::

::::{grid-item-card} {bdg-danger}`Critical`
Malicious patterns detected. `eval()`, `exec()`, known CVEs.
::::

:::::

## Health Scoring

Health score is calculated from 0-100 based on:

```python
def calculate_health_score(server):
    score = 0

    # Repository metrics (40 points)
    score += min(server.stars / 100, 20)
    score += min(server.forks / 50, 10)
    score += 10 if server.open_issues < 10 else 0

    # Documentation (20 points)
    score += 20 if server.readme_content else 0

    # Activity (20 points)
    score += 20 if recent_activity(server) else 0

    # Security (20 points)
    score += 20 if server.risk_level == "safe" else 0
    score += 10 if server.risk_level == "moderate" else 0

    return min(score, 100)
```

## Embedding Generation

MCPS generates vector embeddings for semantic search.

### Model

- **OpenAI text-embedding-3-small**
- **Dimensions:** 1536
- **Cost:** ~$0.02 per 1M tokens

### Use Cases

```python
from packages.harvester.embeddings import semantic_search

# Find similar tools
results = semantic_search(
    query="file system operations",
    top_k=10
)

for tool, similarity in results:
    print(f"{tool.name}: {similarity:.2f}")
```

## Query Examples

### High-Risk Servers

```sql
SELECT name, risk_level, stars
FROM server
WHERE risk_level IN ('high', 'critical')
ORDER BY stars DESC;
```

### Healthy Servers

```sql
SELECT name, health_score, stars
FROM server
WHERE health_score > 80
  AND risk_level = 'safe'
ORDER BY health_score DESC
LIMIT 10;
```

## See Also

- [Data Dictionary](../data-dictionary.md)
- [Architecture](../architecture.md)
- [API Reference](../api/analysis.md)
