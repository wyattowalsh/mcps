# AGENTS.md - Analysis Module Guide

## Context

The `packages/harvester/analysis/` directory provides deep code analysis capabilities for security risk assessment, semantic search, and maintainability metrics. It implements static code analysis using AST (Abstract Syntax Tree) parsing to detect dangerous patterns without executing untrusted code.

**Key Responsibilities:**
- Static security analysis (Python and TypeScript/JavaScript)
- Risk level calculation based on detected patterns
- Semantic embeddings generation for similarity search
- Bus factor calculation (contributor analysis)
- Dependency graph analysis

## Key Files

| File | Purpose |
|------|---------|
| `ast_analyzer.py` | AST-based security pattern detection for Python and TypeScript |
| `embeddings.py` | Semantic vector generation for tools and resources |
| `bus_factor.py` | Contributor diversity and maintainability metrics |

## Patterns

### 1. AST-Based Security Analysis

MCPS uses Abstract Syntax Tree parsing to analyze code statically without execution:

```python
# For Python code
import ast

class PythonASTAnalyzer(ast.NodeVisitor):
    def visit_Call(self, node):
        """Detect dangerous function calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__"}:
                self.dangerous_patterns.append(f"Dangerous call: {node.func.id}()")

    def visit_Import(self, node):
        """Detect dangerous module imports."""
        for alias in node.names:
            if "subprocess" in alias.name:
                self.dangerous_patterns.append(f"Subprocess import: {alias.name}")
```

For TypeScript/JavaScript, regex patterns are used:
```python
class TypeScriptAnalyzer:
    def __init__(self):
        self.patterns = {
            "child_process": re.compile(r"require\(['\"]child_process['\"]\)"),
            "exec": re.compile(r"\bexec\s*\("),
            "eval": re.compile(r"\beval\s*\("),
        }
```

### 2. Risk Scoring Algorithm

Risk levels calculated based on detected patterns:

```python
def calculate_risk_score(patterns: List[str]) -> RiskLevel:
    """Calculate risk level from detected patterns.

    Risk scoring:
        - CRITICAL: eval(), exec() detected
        - HIGH: Subprocess execution + (network OR filesystem)
        - MODERATE: Network or filesystem operations only
        - SAFE: No dangerous patterns detected
    """
    if not patterns:
        return RiskLevel.SAFE

    pattern_text = " ".join(patterns).lower()

    # Check for critical patterns
    if "eval()" in pattern_text or "exec()" in pattern_text:
        return RiskLevel.CRITICAL

    # Check for dangerous combinations
    has_subprocess = any(k in pattern_text for k in ["subprocess", "exec", "spawn"])
    has_network = any(k in pattern_text for k in ["network", "http", "fetch"])
    has_filesystem = any(k in pattern_text for k in ["filesystem", "write"])

    if has_subprocess and (has_network or has_filesystem):
        return RiskLevel.HIGH

    if has_subprocess:
        return RiskLevel.HIGH

    if has_network or has_filesystem:
        return RiskLevel.MODERATE

    return RiskLevel.MODERATE
```

### 3. Semantic Embeddings

Generate vector embeddings for semantic search:

```python
from packages.harvester.analysis.embeddings import generate_embedding

async def create_tool_embedding(tool: Tool) -> ToolEmbedding:
    """Generate embedding for tool description."""
    # Combine name and description for richer context
    text = f"{tool.name}: {tool.description}"

    # Generate 1536-dim vector using OpenAI
    vector = await generate_embedding(text, model="text-embedding-3-small")

    return ToolEmbedding(
        tool_id=tool.id,
        vector=vector,
        model_name="text-embedding-3-small"
    )
```

### 4. Bus Factor Calculation

Measure project maintainability based on contributor diversity:

```python
def calculate_bus_factor(contributors: List[Contributor]) -> int:
    """Calculate bus factor (minimum contributors covering 50% of work).

    Lower bus factor = higher risk (fewer critical contributors)
    Higher bus factor = lower risk (more distributed work)

    Returns:
        Number of contributors needed to cover 50% of total work
    """
    if not contributors:
        return 0

    # Sort by contribution count
    sorted_contributors = sorted(contributors, key=lambda c: c.commits, reverse=True)
    total_commits = sum(c.commits for c in contributors)
    threshold = total_commits * 0.5

    cumulative_commits = 0
    bus_factor = 0

    for contributor in sorted_contributors:
        cumulative_commits += contributor.commits
        bus_factor += 1
        if cumulative_commits >= threshold:
            break

    return bus_factor
```

## AST Scanning Best Practices

### 1. Never Import Untrusted Code

```python
# NEVER do this:
# import untrusted_module  # Executes code!

# ALWAYS do this:
import ast

code = Path("untrusted.py").read_text()
tree = ast.parse(code)
analyzer = PythonASTAnalyzer()
analyzer.visit(tree)
patterns = analyzer.get_dangerous_patterns()
```

### 2. Handle Syntax Errors Gracefully

```python
def analyze(self, code: str) -> List[str]:
    """Analyze code and handle syntax errors."""
    self.dangerous_patterns = []

    try:
        tree = ast.parse(code)
        self.visit(tree)
    except SyntaxError as e:
        logger.warning(f"Failed to parse Python code: {e}")
        self.dangerous_patterns.append(f"Syntax error: {str(e)}")

    return self.dangerous_patterns
```

### 3. Check Multiple Pattern Types

```python
# Check for direct calls
if isinstance(node.func, ast.Name):
    if node.func.id == "eval":
        self.dangerous_patterns.append("eval() call")

# Check for method calls
elif isinstance(node.func, ast.Attribute):
    if node.func.attr in {"system", "popen"}:
        self.dangerous_patterns.append(f"{node.func.attr}() call")
```

### 4. Detect Import Patterns

```python
def visit_ImportFrom(self, node: ast.ImportFrom):
    """Detect dangerous from...import statements."""
    if node.module == "subprocess":
        imported = [alias.name for alias in node.names]
        if any(name in imported for name in ["run", "Popen", "call"]):
            pattern = f"Subprocess import: from subprocess import {', '.join(imported)}"
            self.dangerous_patterns.append(pattern)
```

## Security Pattern Detection

### Dangerous Python Patterns

```python
DANGEROUS_PATTERNS = {
    # Code execution
    "eval()": "Dynamic code evaluation",
    "exec()": "Dynamic code execution",
    "compile()": "Dynamic compilation",
    "__import__()": "Dynamic import",

    # Subprocess execution
    "subprocess.run()": "Shell command execution",
    "subprocess.Popen()": "Process spawning",
    "os.system()": "Shell command execution",
    "os.popen()": "Pipe to shell command",

    # Network access
    "socket": "Network socket operations",
    "requests": "HTTP requests",
    "urllib": "URL handling and fetching",
    "httpx": "Async HTTP requests",

    # Filesystem access
    "os.remove()": "File deletion",
    "shutil.rmtree()": "Directory deletion",
    "open(mode='w')": "File writing",
}
```

### Dangerous TypeScript/JavaScript Patterns

```python
DANGEROUS_TS_PATTERNS = {
    # Code execution
    "eval()": "Dynamic code evaluation",
    "Function()": "Dynamic function creation",
    "vm.runInNewContext()": "Code execution in VM",

    # Subprocess execution
    "child_process.exec()": "Shell command execution",
    "child_process.spawn()": "Process spawning",
    "child_process.execSync()": "Synchronous shell execution",

    # Filesystem access
    "fs.writeFile()": "File writing",
    "fs.unlink()": "File deletion",
    "fs.rmdir()": "Directory deletion",

    # Network access
    "http.request()": "HTTP requests",
    "fetch()": "Network requests",
    "net.connect()": "TCP connections",
}
```

## Embedding Service Usage

### Generating Embeddings

```python
from packages.harvester.analysis.embeddings import EmbeddingService

async def generate_embeddings_for_tools(tools: List[Tool]) -> List[ToolEmbedding]:
    """Generate embeddings for a list of tools."""
    service = EmbeddingService()
    embeddings = []

    for tool in tools:
        # Combine name and description for richer embeddings
        text = f"{tool.name}: {tool.description or ''}"

        try:
            vector = await service.generate_embedding(text)
            embedding = ToolEmbedding(
                tool_id=tool.id,
                vector=vector,
                model_name="text-embedding-3-small"
            )
            embeddings.append(embedding)
        except Exception as e:
            logger.error(f"Failed to generate embedding for {tool.name}: {e}")

    return embeddings
```

### Semantic Search

```python
async def search_similar_tools(query: str, limit: int = 10) -> List[Tool]:
    """Find tools similar to query using vector similarity."""
    # Generate query embedding
    service = EmbeddingService()
    query_vector = await service.generate_embedding(query)

    # Search using sqlite-vec
    # (Actual implementation depends on sqlite-vec integration)
    results = await session.execute(
        """
        SELECT tool_id, distance
        FROM tool_embeddings
        ORDER BY vector <-> ?
        LIMIT ?
        """,
        (query_vector, limit)
    )

    return results
```

## Bus Factor Calculation

### Implementation

```python
from packages.harvester.analysis.bus_factor import calculate_bus_factor

def analyze_maintainability(server: Server) -> Dict[str, Any]:
    """Analyze server maintainability metrics."""
    bus_factor = calculate_bus_factor(server.contributors)

    # Interpret bus factor
    if bus_factor == 1:
        risk = "CRITICAL"  # Single point of failure
        recommendation = "Project relies on one contributor"
    elif bus_factor <= 2:
        risk = "HIGH"
        recommendation = "Limited contributor diversity"
    elif bus_factor <= 5:
        risk = "MODERATE"
        recommendation = "Reasonable contributor diversity"
    else:
        risk = "LOW"
        recommendation = "Good contributor diversity"

    return {
        "bus_factor": bus_factor,
        "risk": risk,
        "recommendation": recommendation,
        "total_contributors": len(server.contributors),
    }
```

### Integration with Health Score

```python
def enhanced_health_score(server: Server) -> int:
    """Calculate health score including bus factor."""
    base_score = calculate_base_health_score(server)

    # Adjust based on bus factor
    bus_factor = calculate_bus_factor(server.contributors)

    if bus_factor >= 5:
        base_score += 10  # Bonus for good diversity
    elif bus_factor <= 2:
        base_score -= 10  # Penalty for low diversity

    return max(0, min(100, base_score))
```

## Examples

### Example 1: Analyze Python File

```python
from pathlib import Path
from packages.harvester.analysis.ast_analyzer import analyze_file

# Analyze a Python file
patterns, risk_level = analyze_file(Path("server.py"))

print(f"Detected patterns: {patterns}")
print(f"Risk level: {risk_level.value}")

# Example output:
# Detected patterns: ['Subprocess execution: subprocess.run()', 'Network module: requests']
# Risk level: high
```

### Example 2: Analyze TypeScript File

```python
from packages.harvester.analysis.ast_analyzer import TypeScriptAnalyzer

code = """
import { exec } from 'child_process';

function runCommand(cmd: string) {
    exec(cmd, (error, stdout, stderr) => {
        console.log(stdout);
    });
}
"""

analyzer = TypeScriptAnalyzer()
patterns = analyzer.analyze(code)

print(f"Detected patterns: {patterns}")
# Output: ['Child process import detected', 'Process execution: exec() (1 occurrences)']
```

### Example 3: Generate and Store Embeddings

```python
from packages.harvester.analysis.embeddings import EmbeddingService
from packages.harvester.models.models import Tool, ToolEmbedding

async def process_tools(tools: List[Tool], session: AsyncSession):
    """Generate and store embeddings for tools."""
    service = EmbeddingService()

    for tool in tools:
        text = f"{tool.name}: {tool.description}"
        vector = await service.generate_embedding(text)

        embedding = ToolEmbedding(
            tool_id=tool.id,
            vector=vector,
            model_name="text-embedding-3-small"
        )

        session.add(embedding)

    await session.commit()
```

## Testing

### Test AST Analysis

```python
import pytest
from packages.harvester.analysis.ast_analyzer import PythonASTAnalyzer

def test_detect_eval():
    """Test detection of eval() calls."""
    code = """
def dangerous_function(user_input):
    result = eval(user_input)
    return result
"""

    analyzer = PythonASTAnalyzer()
    patterns = analyzer.analyze(code)

    assert any("eval()" in p for p in patterns)

def test_detect_subprocess():
    """Test detection of subprocess usage."""
    code = """
import subprocess

subprocess.run(['ls', '-la'], check=True)
"""

    analyzer = PythonASTAnalyzer()
    patterns = analyzer.analyze(code)

    assert any("subprocess" in p.lower() for p in patterns)
```

## Common Tasks

### 1. Add New Dangerous Pattern

**Steps:**
1. Update pattern detection in `ast_analyzer.py`:
```python
# Add to PythonASTAnalyzer
self.dangerous_modules.add("my_dangerous_module")
```

2. Update risk calculation if needed

3. Add test case

### 2. Integrate New Embedding Model

**Steps:**
1. Update `embeddings.py`:
```python
async def generate_embedding(self, text: str, model: str = "new-model"):
    # Use new model API
    pass
```

2. Update ToolEmbedding model_name field

3. Test with sample data

### 3. Enhance Bus Factor Calculation

**Steps:**
1. Modify calculation in `bus_factor.py`
2. Consider factors like:
   - Recent activity weighting
   - Code ownership distribution
   - Review participation

## Related Areas

- **Adapters:** See `packages/harvester/adapters/AGENTS.md` for integrating analysis into harvest workflow
- **Models:** See `packages/harvester/models/models.py` for ToolEmbedding and related entities
- **Core:** See `packages/harvester/core/AGENTS.md` for BaseHarvester integration
- **Parent Guide:** See `packages/harvester/AGENTS.md` for harvester system overview

## Dependencies

Key packages used:
- **ast** (built-in) - Python AST parsing
- **re** (built-in) - Regular expressions for TypeScript
- **openai** (optional) - Embedding generation
- **numpy** (optional) - Vector operations

## Troubleshooting

### Issue: Syntax Errors in AST Parsing
**Solution:** Wrap ast.parse() in try-except, log error, continue processing

### Issue: Embedding API Rate Limits
**Solution:** Implement batching, caching, and exponential backoff

### Issue: False Positives in Pattern Detection
**Solution:** Add context checking, whitelist safe patterns, adjust scoring

---

**Last Updated:** 2025-11-19
**See Also:** PRD.md Protocol C (Static Analysis), ast_analyzer.py source
