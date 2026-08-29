# Architecture Note: Deterministic Code & Representation Synchronization (PyDocSync / ReproSync)

**Document ID**: `ideas/arch_deterministic_pydocsync.md`  
**Status**: Ratified / PoC Design  
**Date**: 2026-08-29  
**Decision Record**: DR-001  
**Target Package Location**: `packages/pypydocsync/` (Standalone Portable Library inside Logseq Repo)  

---

## 1. Executive Context & Thesis

### The Core Problem in AI-Agentic Development
AI coding agents modify code implementations faster than traditional review and documentation workflows can detect semantic drift. Existing linters and test suites check static syntax, type boundaries, and runtime execution, but they lack a **deterministic mechanism to enforce review obligations when maintained representations of software change**.

### Thesis & Positioning
> **"We propose and experimentally evaluate a deterministic representation-synchronization model that gives AI coding agents explicit, machine-verifiable obligations whenever code modifications create potential documentation-review obligations."**

We do not position this as "a SHA-256 tool" or claim "we invented drift detection." Rather, it is an **AST-level deterministic synchronization protocol** designed specifically for AI-agentic governance.

---

## 2. Standalone Package Architecture (`packages/pypydocsync/`)

To ensure this framework can later be extracted, published to GitHub, and reused across any Python project, it is housed in a clean, decoupled folder:

```text
logseq_usage_via_MCP/
├── packages/
│   └── pydocsync/                    <-- Standalone, portable library
│       ├── pyproject.toml          <-- Independent package definition
│       ├── README.md               <-- Standalone library documentation
│       ├── pydocsync/
│       │   ├── __init__.py
│       │   ├── ast_extract.py      <-- AST decomposition & normalization
│       │   ├── fingerprint.py      <-- Multi-representation fingerprinting
│       │   ├── classifier.py       <-- AST Change Impact Classifier
│       │   ├── baseline.py         <-- Distributed JSON lockfile engine
│       │   ├── cli.py              <-- CLI review acknowledgment handler
│       │   └── report.py           <-- Machine-readable AI agent output
│       └── tests/
│           ├── test_synthetic.py   <-- Synthetic edge-case test suite
│           └── test_classifier.py  <-- Impact classifier unit tests
├── logseq_toolkit/                 <-- Real project Layer-1 domain code
├── .specify/                       <-- Root SDD infrastructure & contracts
└── AGENTS.md
```

---

## 3. System Architecture & End-to-End Governance Flows

### 3.1 Architecture Layers (Components)

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │ LAYER 1: Mature Tooling Baseline                                            │
 │ - Ruff: Fast linting, formatting, and docstring structure (PEP 257)         │
 │ - mypy / Pyright: Static type checking (--disallow-untyped-defs)            │
 │ - pydoclint: Strict 100% parity between function signatures and docstrings  │
 │ - pytest --doctest-modules: Executable docstring Examples verification      │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │ LAYER 2: Independent Representation Fingerprints (Python ast + hashlib)     │
 │ - CODE_FINGERPRINT: Normalized implementation body                          │
 │ - API_FINGERPRINT: Parameter names, ordering, defaults, kwargs              │
 │ - TYPE_FINGERPRINT: Parameter and return type annotations                   │
 │ - DOC_FINGERPRINT: Normalized docstring content                             │
 │ - RAISE_TYPE_FINGERPRINT: Exception class names                             │
 │ - RAISE_DETAIL_FINGERPRINT: Normalized exception message string literals    │
 │ - EXAMPLE_FINGERPRINT: Runnable doctest code blocks                         │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │ LAYER 3: AST Change Impact Classifier                                       │
 │ - Evaluates AST deltas against "Candidate Behaviorally Significant Changes" │
 │ - Hypothesized Low Impact: variable renames, loop swaps, helper extract     │
 │ - High Impact (Review Trigger): constants/thresholds (timeout, retries),    │
 │   defaults, new exception messages/types, branching return paths            │
 ├─────────────────────────────────────────────────────────────────────────────┤
 │ LAYER 4: Agent Governance & Review Acknowledgment                           │
 │ - Emits PYPYDOCSYNC001 machine-readable failure payloads for AI agent actions   │
 │ - Explicit CLI Acknowledgment Protocol for audited no-doc-change edits      │
 │ - Future: CKG integration for transitive caller impact analysis             │
 └─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3.2 Runtime Change Detection & AI Governance Flow

```text
                         AI AGENT OR DEVELOPER
                                  │
                          modifies Python code
                                  │
                                  ▼
                        Python AST Extraction
                                  │
       ┌───────────┬──────────────┼──────────────┬───────────┐
       ▼           ▼              ▼              ▼           ▼
      CODE        API            TYPE          RAISE        DOC
  FINGERPRINT FINGERPRINT    FINGERPRINT    FINGERPRINT FINGERPRINT
       │           │              │        (Type/Detail)     │
       └───────────┴──────────────┼──────────────┴───────────┘
                                  │
                                  ▼
                   Compare with Baseline (.project/)
                                  │
                                  ▼
                    AST Change Impact Classifier
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼ (Candidate Low Impact)  ▼ (High Impact)           ▼ (Unknown / Unclassified)
   [Candidate Safe Refactor]  [Behaviorally Significant] [Complex / Ambiguous AST]
   - Variable rename          - Constants / Thresholds   - Deep metaprogramming
   - Expression equivalence   - Default value changed    - Complex generator/yield
   - Pure structural tweak    - Exception type/detail    - Dynamic decorators
        │                     - Branching return paths      │
        │                                 │                 │
        │                                 ▼                 │
        │                       Is DOC_FINGERPRINT changed? │
        │                                 │                 │
        │                        ┌────────┴────────┐        │
        │                        ▼ (Yes)           ▼ (No)   │
        │                  [Doc Updated]     [Doc Unchanged]│
        │                        │                 │        │
        │                        │                 ▼        ▼
        │                        │     🚨 Review Trigger (FAIL)
        │                        │     "Documentation Review
        │                        │      Required for Symbol"
        │                        │                 │
        │                        │         AI / Human Review
        │                        │                 │
        │                        │        ┌────────┴────────┐
        │                        │        ▼ (Needs update)  ▼ (Still accurate)
        │                        │   Update docstring   CLI Acknowledge:
        │                        │        │             `pypydocsync accept`
        │                        │        │                 │
        └────────────────────────┼────────┴─────────────────┘
                                 │
                                 ▼
                Ruff + mypy + pydoclint + pytest
                                 │
                                 ▼
                            ALL GREEN ✅
```

---

## 4. Fingerprint Normalization & Detail Handling

| Fingerprint | Extracted AST Data | Excluded / Ignored |
|---|---|---|
| **`CODE_FINGERPRINT`** | Normalized statements, control flow, AST node types | Whitespace, formatting, comments, docstring |
| **`API_FINGERPRINT`** | Parameter names, order, kinds (pos/kw), default values | Docstring text, internal body |
| **`TYPE_FINGERPRINT`** | Type annotations on args, `*args`, `**kwargs`, return | Function body, default values |
| **`DOC_FINGERPRINT`** | Trimmed, normalized docstring text | Leading/trailing margin whitespace |
| **`RAISE_TYPE`** | Exception class names (e.g. `ValueError`, `KeyError`) | Exception message string literals |
| **`RAISE_DETAIL`** | Normalized exception message string literals & constraints | Dynamic f-string variable substitutions |
| **`EXAMPLE_FINGERPRINT`** | Python doctest prompt lines (`>>>`) and expected outputs | Surrounding markdown formatting |

---

## 5. Candidate Impact Categories (To Validate in PoC)

The classifier operates on hypotheses subject to empirical validation during the PoC:

### Candidate High-Impact Changes (Review Triggers):
- **Constants & Configuration Thresholds**: `TIMEOUT = 30 → 60`, `MAX_RETRIES = 3 → 5`, `MAX_BLOCK_SIZE`.
- **Default Argument Values**: `def parse(path, timeout=30)` → `def parse(path, timeout=60)`.
- **Exception Type or Detail**: New `raise` statement or altered constraint string literal.
- **Control-Flow / Return Paths**: New branching conditions (`if/elif/else`) yielding different returns.

### Candidate Low-Impact Transformations (Subject to PoC Validation):
- **Local Variable Renames**: `total = price + tax` → `sum_val = price + tax`.
- **Expression Equivalence**: `a + b` → `sum((a, b))`.
- **Loop Structure Rewrites**: `for ... in ...` → list comprehension.
- **Private Helper Extraction**: Breaking long functions into local `_helper()` calls (monitored in PoC for side effects).

---

## 6. Explicit Review Acknowledgment Protocol

When a change is classified as a review trigger, but the AI agent or developer verifies that the existing documentation remains 100% accurate:

```bash
python packages/pypydocsync/pydocsync/cli.py accept \
  --symbol logseq_toolkit.parser.parse_block \
  --reason "Refactored parsing loop; output format and error constraints unchanged"
```

### Invariants:
1. **Mandatory Auditable Reason**: The `--reason` string is required and saved into the baseline metadata.
2. **Symbol-Scoped**: Updates the lockfile for only the specific symbol reviewed.
3. **No Silent Auto-Approvals**: The system never self-approves baseline drifts.

---

## 7. Distributed Baseline Storage (`.project/pypydocsync/`)

To prevent Git merge conflicts in parallel AI agent and branching workflows, baselines are saved modularly:

```text
.project/
  └── pydocsync/
      ├── logseq_toolkit/
      │   ├── parser.json
      │   └── ast_nodes.json
      └── mcp_server/
          └── tools.json
```

---

## 8. Hybrid Proof of Concept (PoC) Plan & Failure Case Logging

The PoC will evaluate **20–50 Python functions** across two suites:
1. **Synthetic Edge Cases (`packages/pypydocsync/tests/synthetic/`)**:
   - 15 controlled cases covering: decorators, async functions, generators, `@property`, `@overload`, dataclasses, default arguments, nested functions, lambdas, and exception message alterations.
2. **Real Production Domain Code (`logseq_toolkit/`)**:
   - Live AST parser, block extractors, and MCP tool handlers.

### Empirical Evidence Collection Table (Public Research Asset):
For every transformation tested, record:
| Test Case ID | Code Transformation | Expected Classification | Actual Classification | Doc Actually Affected? | False Pos? | False Neg? | Analysis / Cause |
|---|---|---|---|---|---|---|---|
| `TC-01` | Default arg `timeout=30 → 60` | High Impact | High Impact | Yes | No | No | Detected in API_FINGERPRINT |
| `TC-02` | Variable rename `x` → `val` | Low Impact | Low Impact | No | No | No | Stripped by AST normalizer |

---

## 9. Future Roadmap: Transitive CKG Integration

In Phase 2, integrate with the Code Knowledge Graph (Spashta CKG):
```text
normalize_block() changed (Callee)
        ↓ Spashta CKG
parse_block() caller identified
        ↓
Check if parse_block() docstring contains references to normalize_block() contract
        ↓
Trigger upstream documentation review candidate
```
