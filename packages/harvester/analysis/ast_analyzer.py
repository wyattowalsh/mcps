"""Static code analysis for security risk assessment.

This module provides AST-based analysis for Python and TypeScript code
to detect potentially dangerous patterns and calculate risk scores.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional, Set

from loguru import logger

from packages.harvester.core.models import RiskLevel


class PythonASTAnalyzer(ast.NodeVisitor):
    """AST-based analyzer for Python code security patterns.

    Uses Python's ast module to walk syntax trees and detect potentially
    dangerous function calls and imports.
    """

    def __init__(self) -> None:
        """Initialize the analyzer with empty pattern tracking."""
        self.dangerous_patterns: List[str] = []
        self.dangerous_calls: Set[str] = {"eval", "exec", "__import__", "compile"}
        self.dangerous_modules: Set[str] = {
            "socket",
            "requests",
            "urllib",
            "httpx",
            "subprocess",
            "os.system",
        }
        self.filesystem_modules: Set[str] = {"os", "pathlib", "shutil"}

    def visit_Call(self, node: ast.Call) -> None:
        """Visit Call nodes to detect dangerous function calls.

        Args:
            node: AST Call node to analyze
        """
        # Check for direct dangerous calls like eval(), exec()
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.dangerous_calls:
                pattern = f"Dangerous call: {func_name}()"
                self.dangerous_patterns.append(pattern)
                logger.debug(f"Detected: {pattern}")

        # Check for subprocess.run, subprocess.Popen, etc.
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                attr_name = node.func.attr

                if module_name == "subprocess" and attr_name in {
                    "run",
                    "Popen",
                    "call",
                    "check_output",
                }:
                    pattern = f"Subprocess execution: subprocess.{attr_name}()"
                    self.dangerous_patterns.append(pattern)
                    logger.debug(f"Detected: {pattern}")

                elif module_name == "os" and attr_name in {"system", "popen", "spawn"}:
                    pattern = f"OS command execution: os.{attr_name}()"
                    self.dangerous_patterns.append(pattern)
                    logger.debug(f"Detected: {pattern}")

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit Import nodes to detect dangerous module imports.

        Args:
            node: AST Import node to analyze
        """
        for alias in node.names:
            module_name = alias.name

            # Check for dangerous network modules
            if any(danger in module_name for danger in self.dangerous_modules):
                pattern = f"Network/System import: {module_name}"
                self.dangerous_patterns.append(pattern)
                logger.debug(f"Detected: {pattern}")

            # Check for filesystem modules
            elif any(fs in module_name for fs in self.filesystem_modules):
                pattern = f"Filesystem import: {module_name}"
                self.dangerous_patterns.append(pattern)
                logger.debug(f"Detected: {pattern}")

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit ImportFrom nodes to detect dangerous module imports.

        Args:
            node: AST ImportFrom node to analyze
        """
        if node.module:
            module_name = node.module

            # Check for dangerous imports
            if any(danger in module_name for danger in self.dangerous_modules):
                imported = ", ".join(alias.name for alias in node.names)
                pattern = f"Network/System import: from {module_name} import {imported}"
                self.dangerous_patterns.append(pattern)
                logger.debug(f"Detected: {pattern}")

            # Check for subprocess imports
            elif module_name == "subprocess":
                imported = [alias.name for alias in node.names]
                if any(name in imported for name in ["run", "Popen", "call", "check_output"]):
                    pattern = f"Subprocess import: from subprocess import {', '.join(imported)}"
                    self.dangerous_patterns.append(pattern)
                    logger.debug(f"Detected: {pattern}")

        self.generic_visit(node)

    def analyze(self, code: str) -> List[str]:
        """Analyze Python code and return detected dangerous patterns.

        Args:
            code: Python source code to analyze

        Returns:
            List of detected dangerous patterns
        """
        self.dangerous_patterns = []

        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            logger.warning(f"Failed to parse Python code: {e}")
            self.dangerous_patterns.append(f"Syntax error: {str(e)}")

        return self.dangerous_patterns

    def get_dangerous_patterns(self) -> List[str]:
        """Get the list of detected dangerous patterns.

        Returns:
            List of dangerous patterns found during analysis
        """
        return self.dangerous_patterns


class TypeScriptAnalyzer:
    """Regex-based analyzer for TypeScript/JavaScript code.

    Provides fallback analysis using regular expressions when full
    AST parsing is not available.
    """

    def __init__(self) -> None:
        """Initialize the analyzer with regex patterns."""
        self.dangerous_patterns: List[str] = []

        # Compile regex patterns for common dangerous operations
        self.patterns = {
            "child_process": re.compile(
                r"require\(['\"]child_process['\"]\)|import.*from\s+['\"]child_process['\"]"
            ),
            "exec": re.compile(r"\bexec\s*\("),
            "spawn": re.compile(r"\bspawn\s*\("),
            "eval": re.compile(r"\beval\s*\("),
            "bun_ffi": re.compile(r"require\(['\"]bun:ffi['\"]\)|import.*from\s+['\"]bun:ffi['\"]"),
            "fs_write": re.compile(r"\.(writeFile|writeFileSync|appendFile|appendFileSync)\s*\("),
            "net": re.compile(r"require\(['\"]net['\"]\)|import.*from\s+['\"]net['\"]"),
            "http": re.compile(r"require\(['\"]https?['\"]\)|import.*from\s+['\"]https?['\"]"),
            "fetch": re.compile(r"\bfetch\s*\("),
        }

    def analyze(self, code: str) -> List[str]:
        """Analyze TypeScript/JavaScript code for dangerous patterns.

        Args:
            code: TypeScript/JavaScript source code to analyze

        Returns:
            List of detected dangerous patterns
        """
        self.dangerous_patterns = []

        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(code)
            if matches:
                if pattern_name == "child_process":
                    self.dangerous_patterns.append("Child process import detected")
                    logger.debug("Detected: child_process module")
                elif pattern_name == "exec":
                    self.dangerous_patterns.append(
                        f"Process execution: exec() ({len(matches)} occurrences)"
                    )
                    logger.debug(f"Detected: exec() - {len(matches)} times")
                elif pattern_name == "spawn":
                    self.dangerous_patterns.append(
                        f"Process spawning: spawn() ({len(matches)} occurrences)"
                    )
                    logger.debug(f"Detected: spawn() - {len(matches)} times")
                elif pattern_name == "eval":
                    self.dangerous_patterns.append(
                        f"Code evaluation: eval() ({len(matches)} occurrences)"
                    )
                    logger.debug(f"Detected: eval() - {len(matches)} times")
                elif pattern_name == "bun_ffi":
                    self.dangerous_patterns.append("FFI (Foreign Function Interface) detected")
                    logger.debug("Detected: bun:ffi module")
                elif pattern_name == "fs_write":
                    self.dangerous_patterns.append(
                        f"Filesystem write operations ({len(matches)} occurrences)"
                    )
                    logger.debug(f"Detected: filesystem write - {len(matches)} times")
                elif pattern_name in {"net", "http"}:
                    self.dangerous_patterns.append(f"Network module: {pattern_name}")
                    logger.debug(f"Detected: {pattern_name} module")
                elif pattern_name == "fetch":
                    self.dangerous_patterns.append(
                        f"Network requests: fetch() ({len(matches)} occurrences)"
                    )
                    logger.debug(f"Detected: fetch() - {len(matches)} times")

        return self.dangerous_patterns

    def get_dangerous_patterns(self) -> List[str]:
        """Get the list of detected dangerous patterns.

        Returns:
            List of dangerous patterns found during analysis
        """
        return self.dangerous_patterns


def calculate_risk_score(patterns: List[str]) -> RiskLevel:
    """Calculate risk level based on detected patterns.

    Risk scoring algorithm:
    - CRITICAL: eval() detected or multiple high-risk operations
    - HIGH: Subprocess/shell execution + network + unverified
    - MODERATE: Network or filesystem operations only
    - SAFE: No dangerous patterns detected

    Args:
        patterns: List of detected dangerous patterns

    Returns:
        RiskLevel enum value
    """
    if not patterns:
        logger.debug("No dangerous patterns detected - SAFE")
        return RiskLevel.SAFE

    pattern_text = " ".join(patterns).lower()

    # CRITICAL: Code evaluation is always critical risk
    if "eval()" in pattern_text or "exec()" in pattern_text:
        logger.info(f"CRITICAL risk: Code evaluation detected ({len(patterns)} total patterns)")
        return RiskLevel.CRITICAL

    # Count different categories of dangerous operations
    has_subprocess = any(
        keyword in pattern_text
        for keyword in ["subprocess", "exec", "spawn", "popen", "child_process", "os command"]
    )
    has_network = any(
        keyword in pattern_text for keyword in ["network", "http", "fetch", "socket", "requests"]
    )
    has_filesystem = any(keyword in pattern_text for keyword in ["filesystem", "write", "shutil"])

    # HIGH: Multiple dangerous capabilities combined
    if has_subprocess and (has_network or has_filesystem):
        logger.info(
            f"HIGH risk: Multiple dangerous capabilities detected ({len(patterns)} patterns)"
        )
        return RiskLevel.HIGH

    # HIGH: Subprocess execution alone is high risk
    if has_subprocess:
        logger.info(f"HIGH risk: Subprocess execution detected ({len(patterns)} patterns)")
        return RiskLevel.HIGH

    # MODERATE: Network or filesystem operations
    if has_network or has_filesystem:
        logger.info(
            f"MODERATE risk: Network/filesystem operations detected ({len(patterns)} patterns)"
        )
        return RiskLevel.MODERATE

    # Default to MODERATE if we detected something but it doesn't fit above categories
    logger.info(
        f"MODERATE risk: Unclassified dangerous patterns detected ({len(patterns)} patterns)"
    )
    return RiskLevel.MODERATE


def analyze_file(file_path: Path) -> tuple[List[str], RiskLevel]:
    """Analyze a source code file and return patterns and risk level.

    Args:
        file_path: Path to the source code file

    Returns:
        Tuple of (detected patterns, risk level)
    """
    try:
        code = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return [f"Failed to read file: {str(e)}"], RiskLevel.UNKNOWN

    suffix = file_path.suffix.lower()

    if suffix == ".py":
        analyzer = PythonASTAnalyzer()
        patterns = analyzer.analyze(code)
    elif suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        analyzer = TypeScriptAnalyzer()
        patterns = analyzer.analyze(code)
    else:
        logger.warning(f"Unsupported file type: {suffix}")
        return [f"Unsupported file type: {suffix}"], RiskLevel.UNKNOWN

    risk_level = calculate_risk_score(patterns)

    return patterns, risk_level
