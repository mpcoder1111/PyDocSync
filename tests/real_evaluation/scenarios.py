"""Realistic AI-style development modification scenarios across production symbols.

WHAT IS THIS?
-------------
Contains 15 realistic AI-generated code modification scenarios across 6 development categories:
1. SAFE_REFACTOR: Internal helper extractions and comprehension rewrites.
2. BUG_FIX_THRESHOLD: Threshold, limit, or boundary constant fixes.
3. API_DEFAULT_CHANGE: Default parameter value adjustments.
4. EXCEPTION_ADDITION: New exception types or error checks.
5. TYPE_REFINEMENT: Annotation refinements (e.g. Union -> Optional).
6. DOC_UPDATE: Docstring synchronization and doc-only fixes.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RealProjectScenario:
    scenario_id: str
    target_symbol: str
    category: str
    description: str
    initial_code: str
    modified_code: str
    ai_intended_action: str  # "PASS", "DOC_UPDATE", "CLI_ACCEPT"


REAL_PROJECT_SCENARIOS: list[RealProjectScenario] = [
    # 1. Safe Refactor: List comprehension rewrite in AST extractor
    RealProjectScenario(
        scenario_id="REAL01_EXTRACT_COMPREHENSION",
        target_symbol="ast_extract.strip_leading_docstring",
        category="SAFE_REFACTOR",
        description="Refactored strip docstring check into slice assignment",
        initial_code='''def strip_leading_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    """Remove leading docstring statement from a function/class body list."""
    if not body:
        return body
    first_stmt = body[0]
    if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant) and isinstance(first_stmt.value.value, str):
        return body[1:]
    return body
''',
        modified_code='''def strip_leading_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    """Remove leading docstring statement from a function/class body list."""
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        return body[1:]
    return body
''',
        ai_intended_action="PASS",
    ),

    # 2. Bug Fix / Threshold: Increased max retry constant in parser
    RealProjectScenario(
        scenario_id="REAL02_PARSE_TIMEOUT_THRESHOLD",
        target_symbol="ast_extract.canonicalize_node",
        category="BUG_FIX_THRESHOLD",
        description="Altered internal recursion recursion depth limit from 50 to 100",
        initial_code='''def canonicalize_node(node: ast.AST) -> ast.AST:
    """Create a deep copy of an AST node with stripped location metadata."""
    max_depth = 50
    node_copy = ast.parse(ast.unparse(node)) if hasattr(ast, "unparse") else node
    normalizer = CanonicalASTNormalizer()
    return normalizer.visit(node_copy)
''',
        modified_code='''def canonicalize_node(node: ast.AST) -> ast.AST:
    """Create a deep copy of an AST node with stripped location metadata."""
    max_depth = 100
    node_copy = ast.parse(ast.unparse(node)) if hasattr(ast, "unparse") else node
    normalizer = CanonicalASTNormalizer()
    return normalizer.visit(node_copy)
''',
        ai_intended_action="CLI_ACCEPT",
    ),

    # 3. API Default Change: Changed default root_dir in scan_and_check
    RealProjectScenario(
        scenario_id="REAL03_DEFAULT_ROOT_DIR",
        target_symbol="cli.scan_and_check",
        category="API_DEFAULT_CHANGE",
        description="Changed default root directory from '.' to './src'",
        initial_code='''def scan_and_check(root_dir: Path | str = ".") -> list[SyncFailure]:
    """Scan all Python files in root_dir against baseline lockfiles."""
    root = Path(root_dir)
    mgr = BaselineManager(root_dir=root)
    return []
''',
        modified_code='''def scan_and_check(root_dir: Path | str = "./src") -> list[SyncFailure]:
    """Scan all Python files in root_dir against baseline lockfiles."""
    root = Path(root_dir)
    mgr = BaselineManager(root_dir=root)
    return []
''',
        ai_intended_action="DOC_UPDATE",
    ),

    # 4. Exception Addition: Added ValueError when root dir does not exist
    RealProjectScenario(
        scenario_id="REAL04_RAISE_DIR_NOT_FOUND",
        target_symbol="baseline.BaselineManager.__init__",
        category="EXCEPTION_ADDITION",
        description="Raised ValueError if root directory is not found on disk",
        initial_code='''def __init__(self, root_dir: Path | str = ".") -> None:
    """Initialize manager with project root directory."""
    self.root_dir = Path(root_dir)
    self.baseline_root = self.root_dir / ".project" / "pydocsync"
''',
        modified_code='''def __init__(self, root_dir: Path | str = ".") -> None:
    """Initialize manager with project root directory."""
    self.root_dir = Path(root_dir)
    if not self.root_dir.exists():
        raise ValueError(f"Root dir '{root_dir}' does not exist")
    self.baseline_root = self.root_dir / ".project" / "pydocsync"
''',
        ai_intended_action="DOC_UPDATE",
    ),

    # 5. Type Refinement: Refined return type annotation from list to Sequence
    RealProjectScenario(
        scenario_id="REAL05_TYPE_RETURN_SEQUENCE",
        target_symbol="ast_extract.extract_symbols_from_source",
        category="TYPE_REFINEMENT",
        description="Refined return type annotation from list[SymbolRepresentation] to list[SymbolRepresentation] | None",
        initial_code='''def extract_symbols_from_source(source_code: str) -> list[SymbolRepresentation]:
    """Parse Python source code and extract canonical symbol representations."""
    tree = ast.parse(source_code)
    visitor = SymbolVisitor()
    visitor.visit(tree)
    return visitor.symbols
''',
        modified_code='''def extract_symbols_from_source(source_code: str) -> list[SymbolRepresentation] | None:
    """Parse Python source code and extract canonical symbol representations."""
    if not source_code:
        return None
    tree = ast.parse(source_code)
    visitor = SymbolVisitor()
    visitor.visit(tree)
    return visitor.symbols
''',
        ai_intended_action="DOC_UPDATE",
    ),

    # 6. Doc Update: Updated docstring to match behavior
    RealProjectScenario(
        scenario_id="REAL06_DOCSTRING_CORRECTION",
        target_symbol="report.format_pydocsync001_report",
        category="DOC_UPDATE",
        description="Synchronized docstring with detailed markdown example",
        initial_code='''def format_pydocsync001_report(failures: list[SyncFailure]) -> str:
    """Format sync failures as PYDOCSYNC001 violation message."""
    return f"Violations: {len(failures)}"
''',
        modified_code='''def format_pydocsync001_report(failures: list[SyncFailure]) -> str:
    """Format sync failures into actionable PYDOCSYNC001 machine-readable error blocks.

    Args:
        failures: List of detected representation synchronization failures.

    Returns:
        Formatted multi-line report string with remediation commands.
    """
    return f"Violations: {len(failures)}"
''',
        ai_intended_action="DOC_UPDATE",
    ),

    # 7. Safe Refactor: Renamed local variable in BaselineManager
    RealProjectScenario(
        scenario_id="REAL07_LOCAL_VAR_RENAME_BASELINE",
        target_symbol="baseline.BaselineManager.get_baseline_path",
        category="SAFE_REFACTOR",
        description="Renamed local variable target_path to lockfile_path",
        initial_code='''def get_baseline_path(self, module_rel_path: Path | str) -> Path:
    """Get absolute path to JSON baseline lockfile for a module."""
    mod_path = Path(module_rel_path)
    target_path = self.baseline_root / mod_path.with_suffix(".json")
    return target_path
''',
        modified_code='''def get_baseline_path(self, module_rel_path: Path | str) -> Path:
    """Get absolute path to JSON baseline lockfile for a module."""
    mod_path = Path(module_rel_path)
    lockfile_path = self.baseline_root / mod_path.with_suffix(".json")
    return lockfile_path
''',
        ai_intended_action="PASS",
    ),

    # 8. API Default: Changed enforce_gating default boolean in BaselineManager
    RealProjectScenario(
        scenario_id="REAL08_GATING_DEFAULT_FLAG",
        target_symbol="baseline.BaselineManager.record_symbol_baseline",
        category="API_DEFAULT_CHANGE",
        description="Changed default enforce_gating from False to True",
        initial_code='''def record_symbol_baseline(self, module_rel_path: Path | str, symbol: SymbolRepresentation, fingerprints: FingerprintSet, reason: str, enforce_gating: bool = False) -> None:
    """Record symbol fingerprints to module baseline lockfile."""
    pass
''',
        modified_code='''def record_symbol_baseline(self, module_rel_path: Path | str, symbol: SymbolRepresentation, fingerprints: FingerprintSet, reason: str, enforce_gating: bool = True) -> None:
    """Record symbol fingerprints to module baseline lockfile."""
    pass
''',
        ai_intended_action="DOC_UPDATE",
    ),

    # 9. Exception Addition: Added RuntimeError on baseline corrupted json
    RealProjectScenario(
        scenario_id="REAL09_RAISE_CORRUPT_BASELINE",
        target_symbol="baseline.BaselineManager.load_module_baseline",
        category="EXCEPTION_ADDITION",
        description="Added RuntimeError when baseline JSON contains invalid schema",
        initial_code='''def load_module_baseline(self, module_rel_path: Path | str) -> dict[str, BaselineRecord]:
    """Load baseline records for a module."""
    return {}
''',
        modified_code='''def load_module_baseline(self, module_rel_path: Path | str) -> dict[str, BaselineRecord]:
    """Load baseline records for a module."""
    try:
        return {}
    except Exception as exc:
        raise RuntimeError(f"Corrupted baseline: {exc}") from exc
''',
        ai_intended_action="DOC_UPDATE",
    ),

    # 10. Safe Refactor: Extracted helper function in classifier evaluate loop
    RealProjectScenario(
        scenario_id="REAL10_HELPER_EXTRACTION_CLASSIFIER",
        target_symbol="classifier.ASTChangeImpactClassifier.classify_change",
        category="SAFE_REFACTOR",
        description="Refactored rule loop with early return helper",
        initial_code='''def classify_change(self, old_sym: SymbolRepresentation, new_sym: SymbolRepresentation, old_fp: FingerprintSet, new_fp: FingerprintSet) -> RuleResult:
    """Classify the semantic impact of changes between symbol representations."""
    for rule in self.rules:
        res = rule.evaluate(old_sym, new_sym, old_fp, new_fp)
        if res is not None:
            return res
    return RuleResult(ChangeClassification.UNKNOWN, "RULE_DEFAULT_FALLBACK", "No rule matched", "Fallback")
''',
        modified_code='''def classify_change(self, old_sym: SymbolRepresentation, new_sym: SymbolRepresentation, old_fp: FingerprintSet, new_fp: FingerprintSet) -> RuleResult:
    """Classify the semantic impact of changes between symbol representations."""
    res = next((r.evaluate(old_sym, new_sym, old_fp, new_fp) for r in self.rules if r.evaluate(old_sym, new_sym, old_fp, new_fp) is not None), None)
    if res is not None:
        return res
    return RuleResult(ChangeClassification.UNKNOWN, "RULE_DEFAULT_FALLBACK", "No rule matched", "Fallback")
''',
        ai_intended_action="PASS",
    ),

    # 11. Bug Fix / Threshold: Added support for tuple constants in ThresholdConstantRule
    RealProjectScenario(
        scenario_id="REAL11_THRESHOLD_FLOAT_TOLERANCE",
        target_symbol="classifier.ThresholdConstantRule.evaluate",
        category="BUG_FIX_THRESHOLD",
        description="Added float precision tolerance check threshold (0.001)",
        initial_code='''def evaluate(self, old_sym: SymbolRepresentation, new_sym: SymbolRepresentation, old_fp: FingerprintSet, new_fp: FingerprintSet) -> RuleResult | None:
    """Detect modifications to internal literal constants."""
    if old_fp.code != new_fp.code:
        tolerance = 0.01
        return None
    return None
''',
        modified_code='''def evaluate(self, old_sym: SymbolRepresentation, new_sym: SymbolRepresentation, old_fp: FingerprintSet, new_fp: FingerprintSet) -> RuleResult | None:
    """Detect modifications to internal literal constants."""
    if old_fp.code != new_fp.code:
        tolerance = 0.001
        return None
    return None
''',
        ai_intended_action="CLI_ACCEPT",
    ),

    # 12. Safe Refactor: String formatting modernization
    RealProjectScenario(
        scenario_id="REAL12_FSTRING_MODERNIZATION",
        target_symbol="report.format_symbol_envelope",
        category="SAFE_REFACTOR",
        description="Converted .format() to f-string",
        initial_code='''def format_symbol_envelope(sym_name: str, impact: str) -> str:
    """Format symbol status envelope header."""
    return "Symbol: {} | Impact: {}".format(sym_name, impact)
''',
        modified_code='''def format_symbol_envelope(sym_name: str, impact: str) -> str:
    """Format symbol status envelope header."""
    return f"Symbol: {sym_name} | Impact: {impact}"
''',
        ai_intended_action="PASS",
    ),

    # 13. API Default: Positional argument converted to keyword-only in accept CLI
    RealProjectScenario(
        scenario_id="REAL13_KEYWORD_ONLY_ACCEPT",
        target_symbol="cli.accept_symbol_review",
        category="API_DEFAULT_CHANGE",
        description="Made audit reason mandatory keyword-only parameter",
        initial_code='''def accept_symbol_review(symbol_qualname: str, reason: str, root_dir: Path | str = ".") -> bool:
    """Explicitly record review acknowledgment for a symbol."""
    return True
''',
        modified_code='''def accept_symbol_review(symbol_qualname: str, *, reason: str, root_dir: Path | str = ".") -> bool:
    """Explicitly record review acknowledgment for a symbol."""
    return True
''',
        ai_intended_action="DOC_UPDATE",
    ),

    # 14. Exception Addition: Added FileNotFoundError on missing python file
    RealProjectScenario(
        scenario_id="REAL14_RAISE_FILE_NOT_FOUND",
        target_symbol="cli.scan_and_check",
        category="EXCEPTION_ADDITION",
        description="Raised FileNotFoundError when root_dir does not exist",
        initial_code='''def scan_and_check(root_dir: Path | str = ".") -> list[SyncFailure]:
    """Scan all Python files in root_dir against baseline lockfiles."""
    root = Path(root_dir)
    return []
''',
        modified_code='''def scan_and_check(root_dir: Path | str = ".") -> list[SyncFailure]:
    """Scan all Python files in root_dir against baseline lockfiles."""
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {root_dir}")
    return []
''',
        ai_intended_action="DOC_UPDATE",
    ),

    # 15. Doc Update: Clarified parameter meaning in docstring
    RealProjectScenario(
        scenario_id="REAL15_DOC_PARAMETER_CLARIFICATION",
        target_symbol="baseline.BaselineRecord.to_dict",
        category="DOC_UPDATE",
        description="Added docstring parameter notes for serialized dict output",
        initial_code='''def to_dict(self) -> dict[str, Any]:
    """Convert baseline record to JSON-serializable dictionary."""
    return {}
''',
        modified_code='''def to_dict(self) -> dict[str, Any]:
    """Convert baseline record to JSON-serializable dictionary with SHA-256 fingerprint representations."""
    return {}
''',
        ai_intended_action="DOC_UPDATE",
    ),
]
