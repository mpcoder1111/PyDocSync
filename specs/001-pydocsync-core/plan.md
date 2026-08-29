# Implementation Plan: 001-pypydocsync-core

**Branch**: `001-pypydocsync-core` | **Date**: 2026-08-29 | **Spec**: [`specs/001-pypydocsync-core/spec.md`](spec.md)  
**Input**: Feature specification from `specs/001-pypydocsync-core/spec.md`  

---

## Summary

Build a standalone, portable Python library under `packages/pypypydocsync/` providing a deterministic representation-synchronization engine. The library extracts independent AST fingerprints (`CODE`, `API`, `TYPE`, `DOC`, `RAISE_TYPE`, `RAISE_DETAIL`, `EXAMPLE`), classifies AST changes using a change-impact classifier, manages modular JSON baselines in `.project/pypypydocsync/`, and provides an explicit CLI review acknowledgment command (`pypypydocsync accept`) with structured `PYPYDOCSYNC001` test feedback for AI agents.

---

## Technical Context

- **Language / Version**: Python 3.12+ (standard library `ast`, `hashlib`, `pathlib`, `json`, `argparse`).
- **Primary Dependencies**: Zero runtime dependencies outside standard library for core engine; `pytest` for running test suites and guards; `pydoclint`, `ruff`, and `mypy` for mature baseline linters.
- **Storage**: Modular JSON baseline lockfiles in `.project/pypypydocsync/<package>/<module>.json`.
- **Testing Architecture**:
  - **Layer 1**: Fingerprint extraction unit tests (`test_fingerprint.py`).
  - **Layer 2**: AST Change Impact Classifier unit tests (`test_classifier.py`).
  - **Layer 3**: Synchronization integration & baseline tests (`test_sync_integration.py`).
  - **Layer 4**: AI-agent governance & workflow tests (`test_agent_workflow.py`).
- **Target Platform**: OS-agnostic (Windows / macOS / Linux).
- **Project Type**: Standalone portable Python library (`packages/pypypydocsync/`) + project guard integration.
- **Performance Goals**: Scan and verify 50 functions in < 500ms.

---

## Constitution Check

*Constitution: `.specify/memory/constitution.md` | Standards: `.specify/memory/standards/`*

| Gate | Principle | Status | Notes |
|---|---|---|---|
| Does this feature keep business logic pure Python with zero framework coupling? | I. Two-Layer Architecture | **YES** | Standalone package in `packages/pypypydocsync/` uses standard library only. |
| Is a `spec.md` present and complete before this plan was written? | II. Spec-Driven Development | **YES** | `specs/001-pypydocsync-core/spec.md` ratified and updated. |
| Are tests organized in 4 distinct layers and written before implementation? | III. Intent-First / Test Discipline | **YES** | 4-layer test strategy (Fingerprint, Classifier, Integration, Agent Workflow). |
| Does the design enforce atomic, non-destructive state? | VII. Graph & State Safety | **YES** | JSON baselines updated atomically; explicit `--reason` required. |

---

## Canonical Normalization & Representation Contracts

### 1. Canonical AST Normalization (`ast_extract.py`)
To prevent false alarms from compiler AST runtime metadata while preserving structural semantics:
```text
Source Code
   ↓
ast.parse()
   ↓
ast.NodeTransformer:
  - Strip location metadata ONLY (lineno, col_offset, end_lineno, end_col_offset)
  - PRESERVE semantic AST attributes (including ctx: Load vs Store vs Del)
  - Strip leading docstring statement (Expr(value=Constant(value=str)))
   ↓
canonical_ast_dump()
   ↓
hashlib.sha256() → CODE_FINGERPRINT
```

### 2. Extensible Rule-Based Classifier Architecture (`classifier.py`)
Rather than a monolithic `if/elif` block, the classifier uses an extensible **Rule Engine**:
```python
@dataclass
class RuleResult:
    classification: ChangeClassification  # HIGH_IMPACT | CANDIDATE_LOW_IMPACT | UNKNOWN
    rule_id: str                          # e.g., "DEFAULT_ARG_CHANGE", "THRESHOLD_CONSTANT_CHANGE"
    evidence: str                         # e.g., "timeout: 30 -> 60"
    reason: str                           # e.g., "Default parameter value altered"
```
Each rule inspects AST deltas independently. If no rule matches with high confidence, it fail-safes to `UNKNOWN` (`Review Trigger`).

### 3. Precise Boundary Definitions
- **`API_FINGERPRINT`**:
  - Positional-only params (`/`), Positional-or-keyword params, Keyword-only params (`*`), `*args`, `**kwargs`.
  - Default values serialized deterministically (e.g. `timeout=30` → `30`).
- **`TYPE_FINGERPRINT`**:
  - Type annotations, generic types (`list[str]`), Unions (`str | None`), forward references (`'LogseqPage'`), return annotations.
- **`RAISE_TYPE_FINGERPRINT` & `RAISE_DETAIL_FINGERPRINT`**:
  - Extracted from `ast.Raise` nodes.
  - `RAISE_TYPE`: Qualified exception class name (`ValueError`, `KeyError`).
  - `RAISE_DETAIL`: String literal argument in exception constructor (ignoring dynamic f-string variable substitutions).
- **`DOC_FINGERPRINT`**:
  - Extracted from `ast.get_docstring()`, normalized by trimming leading/trailing margins.
- **`EXAMPLE_FINGERPRINT` (Optional)**:
  - Extracted only when runnable doctests are present in the docstring; absence of examples on standard functions is treated as `None` (not a failure).

---

## Project Structure & File Layout

```text
packages/pypypydocsync/
├── pyproject.toml              # Standalone package definition & build config
├── README.md                   # Standalone documentation & usage guide
├── pypydocsync/
│   ├── __init__.py             # Public exports: scan_symbol, classify_delta, sync_status
│   ├── ast_extract.py          # Canonical AST normalization & symbol visitor
│   ├── fingerprint.py          # FingerprintSet generator (CODE, API, TYPE, DOC, RAISE, EXAMPLE)
│   ├── classifier.py           # AST Change Impact Classifier (High / Low / Unknown)
│   ├── baseline.py             # Distributed modular JSON lockfile engine
│   ├── cli.py                  # CLI entrypoint (`pypypydocsync accept`, `pypypydocsync check`, `pypypydocsync init`)
│   └── report.py               # PYPYDOCSYNC001 machine-readable error formatting
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   └── synthetic_cases.py  # 15 controlled Python language edge cases
    ├── test_fingerprint.py     # Layer 1: Unit tests for fingerprinting
    ├── test_classifier.py      # Layer 2: Unit tests for change impact classifier
    ├── test_integration.py     # Layer 3: Integration tests against baseline lifecycle
    └── test_agent_workflow.py  # Layer 4: AI-agent self-correction and CLI accept workflow
```

---

## Four-Layer Testing Architecture

```text
 ┌─────────────────────────────────────────────────────────────┐
 │ Layer 1: Fingerprint Unit Tests (test_fingerprint.py)       │
 │ - Proves canonical AST normalization ignores comments/white-│
 │   space and correctly isolates CODE, API, TYPE, and DOC.    │
 ├─────────────────────────────────────────────────────────────┤
 │ Layer 2: Classifier Unit Tests (test_classifier.py)         │
 │ - Tests 15 synthetic cases (variable renames vs defaults,  │
 │   constants, new raises, altered branching).                │
 ├─────────────────────────────────────────────────────────────┤
 │ Layer 3: Baseline Integration Tests (test_integration.py)   │
 │ - Proves modular JSON baseline saving, symbol updates, and  │
 │   gated baseline creation (refuses baseline for bad docs).  │
 ├─────────────────────────────────────────────────────────────┤
 │ Layer 4: AI Agent Workflow Tests (test_agent_workflow.py)   │
 │ - Proves agent parses PYPYDOCSYNC001, runs `pypypydocsync accept`,    │
 │   updates docstrings, and reaches full green state.         │
 └─────────────────────────────────────────────────────────────┘
```

---

## Phase Execution Roadmap

1. **Phase 0 (Setup & Fixtures)**:
   - Create package directory `packages/pypypydocsync/` with `pyproject.toml`.
   - Build 15 synthetic test fixtures (`tests/fixtures/synthetic_cases.py`).
2. **Phase 1 (AST Extraction & Fingerprinting)**:
   - Implement `ast_extract.py` and `fingerprint.py`.
   - Validate Layer 1 test suite (`test_fingerprint.py`).
3. **Phase 2 (Change Impact Classifier)**:
   - Implement `classifier.py` with High / Candidate Low / Unknown classifications.
   - Validate Layer 2 test suite (`test_classifier.py`).
4. **Phase 3 (Baseline Management & CLI)**:
   - Implement `baseline.py`, `report.py`, and `cli.py`.
   - Validate Layer 3 and Layer 4 integration suites (`test_integration.py`, `test_agent_workflow.py`).
5. **Phase 4 (Empirical Evaluation & PoC Report)**:
   - Run PoC against 20–50 real functions and record false-positive / false-negative findings.
