"""Analysis - AST Parsing, Security Scanning, and Semantic Indexing.

This package contains code analysis tools including:
- AST-based static analysis for Python and TypeScript
- Security risk assessment and pattern detection
- Semantic embeddings for tool descriptions
- Bus factor calculation for maintainer analysis
"""

from packages.harvester.analysis.ast_analyzer import (
    PythonASTAnalyzer,
    TypeScriptAnalyzer,
    calculate_risk_score,
    analyze_file,
)
from packages.harvester.analysis.bus_factor import (
    calculate_bus_factor,
    get_bus_factor_description,
    analyze_contributor_health,
    BusFactor,
)
from packages.harvester.analysis.embeddings import (
    EmbeddingService,
    generate_embedding,
)

__all__ = [
    # AST Analysis
    "PythonASTAnalyzer",
    "TypeScriptAnalyzer",
    "calculate_risk_score",
    "analyze_file",
    # Bus Factor
    "calculate_bus_factor",
    "get_bus_factor_description",
    "analyze_contributor_health",
    "BusFactor",
    # Embeddings
    "EmbeddingService",
    "generate_embedding",
]
