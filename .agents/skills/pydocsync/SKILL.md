---
name: "pydocsync"
description: "Understand and use PyDocSync for deterministic code-documentation synchronization during AI-assisted Python development."
user-invocable: false
disable-model-invocation: false
---

# PyDocSync

## 1. Purpose

PyDocSync is a lightweight, deterministic code–documentation synchronization engine for Python.

It addresses an acute failure mode in AI-assisted software engineering: **silent documentation drift**. When AI coding agents or developers modify implementation details (e.g. changing parameter defaults, altering raised exceptions, restructuring dictionaries, or reordering call sequences), unit tests often still pass, but docstrings and parameter contracts are frequently left unmaintained or become outdated.

PyDocSync solves this by computing multi-representation AST fingerprints and evaluating code changes against a recorded baseline to determine if a documentation review obligation exists.

---

## 2. Project Information

- **Official GitHub Repository**: [`https://github.com/mpcoder1111/PyDocSync`](https://github.com/mpcoder1111/PyDocSync)
- **Current Version**: `0.2.0 Experimental`
- **Supported Python**: Python `3.10+` (zero runtime dependencies, standard library only)

---

## 3. Why This Project Uses PyDocSync

In AI-assisted pair programming and agentic workflows, LLMs modify code rapidly across multiple files. While linters and test suites check for syntax validity and functional correctness, they do not verify if documentation accurately reflects implementation changes.

```text
AI changes implementation
        ↓
Unit tests may still pass
        ↓
Docstring remains unchanged / outdated
        ↓
PyDocSync detects representation mismatch
        ↓
AI reviews & updates docstring (or explicitly accepts)
```

By adding PyDocSync as an automated gate, this project ensures that all Layer-1 Python contracts, models, and MCP tool handlers help maintain synchronized, reviewable documentation without manual auditing overhead.

---

## 4. How It Works: Multi-Representation Fingerprints & Baselines

PyDocSync extracts and normalizes the Abstract Syntax Tree (AST) of every public function, method, and class across 7 distinct representation planes:

1. **`CODE`**: Canonicalized AST execution flow, expressions, and statements (ephemeral source locations like `lineno` and `col_offset` stripped; AST `ctx` semantics preserved).
2. **`API`**: Function signatures, parameter names, ordering, kind (positional, keyword-only), and default values.
3. **`TYPE`**: Type annotations and return type definitions.
4. **`DOC`**: Extracted docstrings (stripped of leading/trailing whitespace).
5. **`RAISE_TYPE`**: Exception classes raised explicitly in the function body (`ast.Raise`).
6. **`RAISE_DETAIL`**: Literal string messages or formatted arguments passed to exceptions.
7. **`EXAMPLE`**: Runnable code examples or doctest snippets embedded within docstrings.

### The Baseline Concept
Before PyDocSync can detect changes, a **baseline** must exist. The baseline is stored as modular JSON lockfiles under `.project/pydocsync/` (with a top-level `schema_version: 1` envelope). It records the SHA-256 fingerprints of all compliant symbols at a known good state.

> **Important Invariant**: PyDocSync produces a **deterministic review signal** (`PYDOCSYNC001`); it does not mathematically prove that natural-language documentation is correct.

---

## 5. Normal Workflow & Decision Tree

> **Workflow Rule**: After any Python modification, follow the mandatory PyDocSync procedure in `AGENTS.md`; this skill provides the conceptual knowledge needed to make the correct decision.

```text
Baseline exists (.project/pydocsync/)
        ↓
AI / Developer modifies Python code
        ↓
Run scoped unit tests (pytest)
        ↓
Run: pydocsync check
        ↓
 ┌──────┴──────────────────────────────────────┐
PASS (Exit 0)                           FAIL (Exit 1: PYDOCSYNC001)
                                               ↓
                                      Inspect evidence & diagnostic
                                               ↓
                             ┌─────────────────┴─────────────────┐
                             ↓                                   ↓
                  Implementation changed              Documentation is
                  contract / behavior                 still 100% accurate
                             ↓                                   ↓
                  Update docstring in code            pydocsync accept
                             ↓                        --symbol <name>
                  Run: pydocsync check                --reason "<rationale>"
                             ↓                                   ↓
                           PASS                                PASS
```

---

## 6. CLI Commands & Lifecycle

### `pydocsync init`
```powershell
pydocsync init
```
- **Purpose**: Scans the codebase and creates or updates baseline lockfiles for all compliant symbols.
- **When to use**: **Only** when onboarding a newly authored module, when the project has no valid baseline, or when deliberately establishing/re-establishing a baseline as an explicit maintenance operation.
- **Safety Invariant**: **NEVER run `init` to fix a `pydocsync check` failure.** Running `init` on modified code overwrites the baseline lockfile and destroys change-detection capabilities.

### `pydocsync check`
```powershell
pydocsync check
```
- **Purpose**: Compares current AST fingerprints against `.project/pydocsync/` baselines.
- **Exit Codes & Inspection**:
  - `0`: All symbols are synchronized.
  - `1`: Synchronization review required (`PYDOCSYNC001`), or a target symbol was not found. **Always inspect the actual diagnostic output before deciding on remediation.**
  - `2`: Invalid CLI arguments, syntax error, or rejected blank audit reason.

### `pydocsync accept`
```powershell
pydocsync accept --symbol <qualname> --reason "<rationale>"
```
- **Purpose**: Explicitly records that a human or AI agent reviewed the changed symbol and verified that the existing documentation remains 100% accurate.
- **Requirements**: Requires a non-empty, descriptive `--reason`. Blank or whitespace reasons are rejected with exit code `2`.
- **Prohibition**: Never use `accept` blindly to silence a check without verifying docstring accuracy.

---

## 7. Programmatic Python API

For embedding in tools, background tasks, or custom MCP verification scripts:

```python
from pydocsync import check, init, accept, SyncResult, SyncFailure

# Run check programmatically
result: SyncResult = check(root_dir=".")

if not result.is_synchronized:
    print(f"Sync review required for {result.failure_count} symbols:")
    for failure in result.failures:
        print(f"  - {failure.symbol.qualname} in {failure.file_path}")
        print(f"    Reason: {failure.rule_result.reason}")
        print(f"    Changed planes: {', '.join(failure.changed_fingerprints)}")

# Accept a reviewed symbol programmatically
success: bool = accept(
    symbol_qualname="mypackage.module.my_function",
    reason="Refactored internal helper; public contract and exceptions unchanged.",
    root_dir="."
)
```

---

## 8. Complementary Ecosystem Role (What PyDocSync Does NOT Do)

PyDocSync works alongside existing Python quality tools, filling a distinct gap:

| Tool | Focus Area | PyDocSync's Relationship |
|---|---|---|
| **`pytest`** | Functional correctness | PyDocSync verifies doc sync, which tests cannot detect. |
| **`ruff` / `flake8`** | Formatting & static linting | PyDocSync checks semantic AST changes across time/baselines. |
| **`mypy` / `pyright`** | Static type checking | PyDocSync tracks changes in type representations (`TYPE`). |
| **`pydoclint`** | Docstring style compliance | PyDocSync verifies that docstrings stay updated when code changes. |

### Known Limitations
1. **No Semantic NLP Proof**: PyDocSync verifies representation alignment and generates review signals; it cannot evaluate whether human language in a docstring is grammatically or semantically sound.
2. **Static AST Boundary**: Static AST analysis cannot track runtime monkey-patching, dynamic reflection (`getattr`/`setattr`), or inter-procedural heap aliasing across external packages. When encountered, PyDocSync safely routes to `UNKNOWN` with `review_required=True`.

---

## 9. When to Read This Skill

An AI agent should activate or reference this skill when:
- Diagnosing a complex `PYDOCSYNC001` failure or analyzing representation diffs.
- Deciding whether a code modification requires a docstring update vs. an `accept` authorization.
- Writing programmatic scripts or MCP tools that interface with PyDocSync.
- Understanding AST representation planes or baseline envelope versioning.

*(For routine daily edits, the compact rules in `AGENTS.md` provide the mandatory commands).*

---

## 10. Project-Specific Usage

This repository installs PyDocSync as an external dependency:
- **Repository**: `https://github.com/mpcoder1111/PyDocSync.git` (`v0.2.0`)
- **CLI Executable**: `.\.venv\Scripts\pydocsync.exe`
- **Scope**: Applied to all Layer-1 Python domain modules, utility classes, and MCP protocol tools.
