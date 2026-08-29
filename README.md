# PyDocSync

**Deterministic Code–Documentation Synchronization for AI-Assisted Python Development**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python: >=3.10](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Status: Experimental 0.2.0](https://img.shields.io/badge/Status-Experimental_0.2.0-orange.svg)]()

> **PyDocSync deterministically detects when Python implementation changes may require corresponding documentation updates or an explicit documentation review.**

PyDocSync is designed for **AI-assisted / agentic coding workflows**. It does not attempt to prove that natural-language documentation is semantically correct.

---

## The Problem

An AI coding agent can modify working Python code, pass tests, and still leave documentation describing the previous implementation.

For example:

```python
def parse_config(path, timeout=30):
    """Parse configuration using the configured timeout."""
```

An AI agent changes the implementation to:

```python
def parse_config(path, timeout=60):
    """Parse configuration using the configured timeout."""
```

The code may be valid. Tests may pass. Type checking may pass.

But the documentation may now be stale.

PyDocSync adds a deterministic check to catch this maintenance gap:

```text
KNOWN INITIAL STATE
       │
       ▼
 pydocsync init
       │
       ▼
   BASELINE
       │
       │
       │   AI agent / developer modifies code
       ▼
 pydocsync check
       │
       ▼
Implementation representation changed
while related documentation did not
       │
       ▼
 PYDOCSYNC001
       │
       ▼
Documentation must be updated
OR the change must be explicitly reviewed
       │
       ▼
      PASS
```

The goal is **not simply to detect that code changed**.

The goal is to deterministically identify changes that may create a **documentation-review obligation**.

---

## Three Layers of Documentation Maintenance

PyDocSync complements established Python quality tools:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer A — Missing Information                                               │
│                                                                             │
│ Missing docstrings, missing type annotations, missing Args/Returns, etc.    │
│                                                                             │
│ Typical tools: Ruff / pydocstyle / pydoclint                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer B — Contract / Signature Drift                                        │
│                                                                             │
│ Function signatures, parameter names, types, Returns, Raises, etc.         │
│ no longer agree with documentation.                                         │
│                                                                             │
│ Typical tools: Mypy / Pyright / pydoclint                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer C — Implementation ↔ Documentation Drift                              │
│                                                                             │
│ Implementation changes while related documentation remains unchanged,       │
│ even when the API/type signature may still appear valid.                    │
│                                                                             │
│ PyDocSync's focus                                                      ✓    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**PyDocSync does not replace Ruff, Mypy, Pyright, pydoclint, or pytest.**

It adds a deterministic synchronization signal for **Layer C**.

---

## How PyDocSync Works

PyDocSync analyzes Python source using the AST and creates separate deterministic SHA-256 fingerprints for different representations of the same function/class.

```text
                         PYTHON SOURCE
                              │
                              ▼
                     ┌─────────────────┐
                     │   AST Analysis  │
                     └────────┬────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
       CODE / API          TYPE / DOC        RAISE / EXAMPLE
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    SHA-256 fingerprints
                              │
                              ▼
                   Versioned baseline state
                              │
                    AI modifies Python code
                              │
                              ▼
                     pydocsync check
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
               PASS                   PYDOCSYNC001
                                           │
                                  Documentation review
                                           │
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
                  Update documentation              Existing documentation
                         │                            is still accurate
                         │                                   │
                         │                            pydocsync accept
                         │                                   │
                         └─────────────────┬─────────────────┘
                                           ▼
                                  pydocsync check
                                           │
                                           ▼
                                         PASS
```

### Seven Representation Planes

The current implementation maintains independent fingerprints for:

```text
CODE
API
TYPE
DOC
RAISE_TYPE
RAISE_DETAIL
EXAMPLE
```

For example, if an AI agent changes a default value and adds a new exception:

```text
BEFORE                       AFTER

CODE          AAAAA          CODE          XXXXX  ← changed
API           BBBBB          API           YYYYY  ← changed
TYPE          CCCCC          TYPE          CCCCC  ← unchanged
DOC           DDDDD          DOC           DDDDD  ← unchanged
RAISE_TYPE    EEEEE          RAISE_TYPE    ZZZZZ  ← changed
```

PyDocSync can therefore provide evidence about **what changed and what related representation did not change**, rather than relying on one opaque whole-function hash.

---

## Deterministic Review, Not Semantic Proof

A fingerprint can deterministically establish that a representation changed.

It cannot prove that a natural-language statement is true.

For example, a hash cannot prove whether:

> "Retries three times before raising an error."

is semantically correct.

Therefore PyDocSync treats a mismatch as a **documentation-review obligation** rather than automatically declaring the documentation incorrect.

When deterministic static analysis cannot safely establish the impact of a change, PyDocSync routes the case to:

```text
UNKNOWN
review_required = True
```

This is intentional: **PyDocSync prefers an explicit review over silently allowing potentially stale documentation.**

---

## Installation

PyDocSync 0.2.0 is an experimental release.

Install directly from GitHub:

```bash
python -m pip install git+https://github.com/mpcoder1111/PyDocSync.git
```

For the `v0.2.0` release tag:

```bash
python -m pip install git+https://github.com/mpcoder1111/PyDocSync.git@v0.2.0
```

A release wheel is also available:

```bash
python -m pip install pydocsync-0.2.0-py3-none-any.whl
```

### Requirements

- Python **3.10 or newer**
- Zero external runtime dependencies (pure standard library)
- Explicitly exercised on Python 3.10, 3.11, 3.12, and 3.13

---

## Quick Start

Run the commands from your Python project root.

### 1. Establish the Initial Baseline

```bash
pydocsync init
```

This creates local baseline state under `.project/pydocsync/`.

The baseline represents the known code/documentation state **before future modifications are checked**.

> [!IMPORTANT]
> Do **not** run `pydocsync init` after every AI modification. The purpose of the baseline is to preserve the state against which subsequent modifications are detected.

### 2. Check the Project

```bash
pydocsync check
```

If the monitored representations are synchronized, it exits with `0` (`PASS`).

### 3. AI Agent Modifies Code

Suppose an AI agent changes:

```python
def parse_config(path, timeout=30):
    """Parse configuration using the configured timeout."""
```

to:

```python
def parse_config(path, timeout=60):
    """Parse configuration using the configured timeout."""
```

The AI agent has modified the **code**, but has not modified the **documentation**.

### 4. Run PyDocSync

```bash
pydocsync check
```

PyDocSync emits a structured diagnostic:

```text
======================================================================
PYDOCSYNC001: 1 symbol(s) require documentation review.
======================================================================

Symbol:     parse_config
File:       src/parser.py:3
Impact:     HIGH_IMPACT
Rule ID:    RULE_DEFAULT_VALUE_CHANGE
Changed:    api, code
Evidence:   defaults changed: ['30'] -> ['60']
Reason:     Default parameter value altered in function signature.
Action:     Update docstring for 'parse_config', or if documentation
            remains 100% accurate, acknowledge via:
            pydocsync accept --symbol parse_config --reason "<audit reason>"
----------------------------------------------------------------------
```

The command returns exit code `1`.

### 5. Update Documentation When Required

If the implementation change affects documented behavior, update the docstring/documentation and run `pydocsync check` again to return to `PASS`.

### 6. Explicitly Accept a Reviewed Change

Sometimes an implementation change is intentional but the existing documentation remains completely accurate (e.g. an internal refactoring or performance optimization).

After reviewing the documentation:

```bash
pydocsync accept --symbol parse_config --reason "Increased default timeout to 60s for high-latency connections; public doc remains accurate."
```

Then `pydocsync check` returns to the clean `PASS` state (exit code `0`).

> [!NOTE]
> **Trust and Authorization Model**:  
> `pydocsync accept` does **not** prove documentation correctness. It serves as an audit record that a human developer or AI agent has reviewed the change and determined the existing doc remains accurate. Non-empty, descriptive audit reasons are strictly required.

---

## How AI Agents Use PyDocSync

PyDocSync does not need to be part of the AI model itself. It serves as a deterministic verification step in the AI agent's coding workflow:

```text
                         AI CODING AGENT
                                │
                                │ modifies code
                                ▼
                    ┌────────────────────────┐
                    │ Tests / Lint / Types   │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │    pydocsync check     │
                    └────────────┬───────────┘
                                 │
                       ┌─────────┴─────────┐
                       ▼                   ▼
                     PASS             PYDOCSYNC001
                                           │
                                    AI reviews signal
                                           │
                           ┌───────────────┴──────────────┐
                           ▼                              ▼
                    Update documentation        Documentation still
                           │                     accurate
                           │                              │
                           │                       pydocsync accept
                           │                              │
                           └──────────────┬───────────────┘
                                          ▼
                                  pydocsync check
                                          │
                                          ▼
                                         PASS
```

---

## Programmatic Python API

PyDocSync provides a minimal, typed Python API for tool builders and IDE extensions:

```python
from pydocsync import check, init, accept, SyncResult, SyncFailure

# Scan working tree
result = check(root_dir=".")

if not result.is_synchronized:
    print(f"Detected {result.failure_count} review obligations:")
    for failure in result.failures:
        print(f"  - {failure.symbol.qualname}: {failure.rule_result.reason}")

# Programmatically acknowledge a reviewed symbol
accept(
    symbol_qualname="mypkg.func",
    reason="Refactored internal algorithm; verified documentation remains accurate.",
    root_dir=".",
)
```

### Supported Public API Surface

The stable public interface for 0.2.0 consists strictly of:
- `check(root_dir=".") -> SyncResult`
- `init(root_dir=".") -> int`
- `accept(symbol_qualname, reason, root_dir=".") -> bool`
- `SyncResult`
- `SyncFailure`
- `__version__ = "0.2.0"`

*Internal implementation modules (`ast_extract`, `fingerprint`, `classifier`, `baseline`, `report`) are private and subject to change.*

---

## Monitored Symbol Policy

By default, PyDocSync monitors:
- **Public Callables**: Top-level functions and class methods not prefixed with `_`.
- **Public Classes**: Top-level classes not prefixed with `_`.

Common non-source/build directories are excluded by default:
```text
tests/
.venv/
__pycache__/
dist/
build/
```

---

## Baseline State & Schema Versioning

PyDocSync stores versioned synchronization state under `.project/pydocsync/`:

```json
{
  "schema_version": 1,
  "pydocsync_version": "0.2.0",
  "fingerprint_algorithm": "sha256",
  "symbols": { ... }
}
```

The baseline is **not a replacement for Git**. Git provides source history and commits; PyDocSync provides normalized representation fingerprints, change classification, and audit records.

---

## External Evaluation Corpora

PyDocSync was evaluated against three unrelated open-source Python projects:
- **Dulwich** — Git engine / protocol and binary parsing code.
- **Janome** — Morphological NLP / tokenizer and dictionary trie code.
- **python-sdb** — Binary serialization and bitwise structure parsing code.

> [!NOTE]
> These projects were used **only as external evaluation corpora**. They are not dependencies, are not bundled in PyDocSync, and received zero project-specific classifier rules.

---

## Empirical Benchmark Results (Observed Metrics)

The following are **observed benchmark metrics**, not claims of universal accuracy:

### 1. Adversarial Stress Testing
- 16 adversarial attack cases under dual execution.
- Addressed evaluation-order and dictionary-key-order blind spots; cataloged heap aliasing as an AST boundary.

### 2. Real-Project Evaluation (67 Symbols, 15 Scenarios)
- Evaluated against production code with dual blind human reviewer consensus (Reviewer A & B).
- **Observed review-trigger recall: 100.0% (11/11).**
- **Observed review-trigger precision: 78.6%.**
- **Unnecessary documentation churn: 0.0%.**
- **Full-package scan time: 49.97 ms.**

### 3. External Multi-Repository Evaluation (61 Symbols, 20 Scenarios)
- Evaluated across Dulwich, Janome, and python-sdb with frozen Classifier v0.2.
- Two independent blind reviewers with 100% agreement.
- **Observed review-trigger recall: 100.0% (13/13).**
- **Observed review-trigger precision: 100.0% (13/13)** for applicable benchmark cases.
- **Unnecessary documentation churn: 0.0%.**
- **UNKNOWN / escalation rate: 15.0% (3/20).**

---

## Exit Codes

```text
0   Clean / synchronized
1   Synchronization review required or operation failed
2   Invalid command usage / missing required arguments
```

---

## License

PyDocSync is open-source software licensed under the [Apache-2.0 License](LICENSE).
