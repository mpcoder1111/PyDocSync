# Feature Specification: 001-pypydocsync-core

## Deterministic Code & Representation Synchronization Framework (PyDocSync PoC)

**Feature Branch**: `001-pypydocsync-core`  
**Created**: 2026-08-29  
**Last updated**: 2026-08-29  
**Status**: Draft  
**Input**: User description & Ratified Architecture Note (`ideas/arch_deterministic_pypydocsync.md`)  

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Alignment with project constitution (Two-Layer, Determinism, Quality Gates) |
| 2 | [User Scenarios & Testing](#user-scenarios--testing) | Prioritized user stories (US1–US4) with testable acceptance scenarios |
| 3 | [Requirements](#requirements) | Functional requirements (FR-001 to FR-012) and key domain entities |
| 4 | [Success Criteria](#success-criteria) | Measurable, verifiable outcomes and PoC evidence targets |
| 5 | [Assumptions & Boundaries](#assumptions--boundaries) | Scope boundaries, runtime assumptions, and dependencies |

---

## Applicable Constitution Principles

*Per project governance (`.specify/memory/constitution.md`):*

| Principle | Applies? | Notes |
|---|---|---|
| **I. Two-Layer Pure Domain Architecture** | **YES** | Standalone domain engine in `packages/pypypydocsync/` with zero web or external transport coupling. |
| **II. Spec-Driven Development (SDD)** | **YES** | This specification is the Principle II artifact initiating Feature 001. |
| **III. Intent-First & Grounded Planning** | **YES** | Directly addresses AI-agent documentation drift with clear user stories and verifiable acceptance criteria. |
| **IV. Pre-Execution Contracts** | **YES** | Standalone tool interface and machine-readable output contracts defined before coding. |
| **V. Deterministic Platform, AI-as-Producer** | **YES** | Core AST normalization and fingerprinting are 100% deterministic pure Python algorithms. |
| **VI. Self-Enforcing Quality Gates** | **YES** | Integrates into `pytest tests/guards/test_doc_sync.py` to prevent unreviewed drift from passing CI. |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deterministic Representation Fingerprinting (Priority: P1)

As a developer or AI coding agent, I want the system to extract and generate independent, deterministic fingerprints (`CODE`, `API`, `TYPE`, `DOC`, `RAISE_TYPE`, `RAISE_DETAIL`, `EXAMPLE`) for any Python function or class method, so that code changes can be inspected along distinct structural dimensions without noise from formatting or comments.

**Why this priority**: Foundational core capability. Without independent normalized fingerprints, change detection and impact classification are impossible.

**Independent Test**: Can be fully tested by parsing a sample Python file with AST, generating fingerprints, reformatting comments/whitespace, and verifying that `CODE_FINGERPRINT` remains 100% byte-identical.

**Acceptance Scenarios**:
1. **Given** a Python function with docstrings and comments, **When** non-semantic whitespace or comments are changed, **Then** `CODE_FINGERPRINT`, `API_FINGERPRINT`, and `DOC_FINGERPRINT` remain identical.
2. **Given** a function where default parameter values change (e.g. `timeout=30 → 60`), **When** fingerprints are generated, **Then** `API_FINGERPRINT` changes while `TYPE_FINGERPRINT` remains identical.
3. **Given** a function with a `raise ValueError("min 3 blocks")`, **When** the error message changes to `"min 5 blocks"`, **Then** `RAISE_TYPE_FINGERPRINT` remains unchanged while `RAISE_DETAIL_FINGERPRINT` changes.

---

### User Story 2 - AST Change Impact Classification (Priority: P1)

As an AI coding agent or CI test runner, I want the system to classify AST code modifications into `High Impact` (behaviorally significant), `Candidate Low Impact` (refactor/structural), or `Unknown/Unclassified` (ambiguous), so that safe internal refactors do not trigger false-positive documentation review failures.

**Why this priority**: Critical differentiator that prevents AI agents from getting stuck in false-positive documentation churn.

**Independent Test**: Feed the classifier 15 synthetic code transformations (e.g., variable renames vs constant threshold changes) and verify that it outputs the expected impact category.

**Acceptance Scenarios**:
1. **Given** an innocent refactor (e.g. variable rename or loop-to-comprehension rewrite), **When** evaluated by the classifier, **Then** it classifies as `Candidate Low Impact` and grants a silent pass without failing tests.
2. **Given** a behaviorally significant change (e.g. `TIMEOUT = 30 → 60`, new branching return condition, or altered exception), **When** the docstring is NOT updated, **Then** it classifies as `High Impact` and issues a `Review Trigger (FAIL)`.
3. **Given** a highly complex or ambiguous AST change (metaprogramming, dynamic decorators), **When** evaluated, **Then** it classifies as `Unknown/Unclassified` and safely defaults to a `Review Trigger`.

---

### User Story 3 - Distributed Baseline Management & Machine-Readable Output (Priority: P2)

As a developer working in Git with parallel branches or AI subagents, I want the synchronization baseline stored modularly per module/package in `.project/pypypydocsync/<package>/<module>.json`, and test failures reported in a structured `PYPYDOCSYNC001` format, so that Git merge conflicts are avoided and AI agents receive actionable instructions.

**Why this priority**: Ensures multi-branch collaboration and gives AI agents clear self-correction signals.

**Independent Test**: Run a test guard on a drifted symbol, parse the `PYPYDOCSYNC001` error output, and verify it contains the symbol name, line number, detected change, unchanged docstring, and required remediation command.

**Acceptance Scenarios**:
1. **Given** a package `logseq_toolkit/parser.py`, **When** the baseline is generated, **Then** it writes to `.project/pypypydocsync/logseq_toolkit/parser.json` without touching other module baselines.
2. **Given** a symbol that fails synchronization, **When** `pytest tests/guards/test_doc_sync.py` runs, **Then** it outputs a `PYPYDOCSYNC001` envelope detailing the exact symbol, file, line number, and action required.

---

### User Story 4 - Explicit CLI Review Acknowledgment (Priority: P2)

As a developer or AI agent who has verified that an intentional implementation change does not alter the documented behavior, I want to execute an explicit CLI command (`pypypydocsync accept --symbol ... --reason "..."`) to acknowledge the change, so that the baseline is updated in an auditable manner without polluting source code with inline comments.

**Why this priority**: Provides a clean, auditable escape hatch when code changes but existing documentation remains completely accurate.

**Independent Test**: Trigger a `High Impact` failure, run the CLI accept command with a valid `--reason`, and verify that subsequent test runs pass.

**Acceptance Scenarios**:
1. **Given** a flagged symbol, **When** `pypypydocsync accept --symbol foo.bar --reason "Refactored loop; contract unchanged"` is executed, **Then** the baseline JSON is updated with the new fingerprints and audit reason, and the guard test passes.
2. **Given** an attempt to run `pypypydocsync accept` without `--reason`, **When** executed, **Then** the CLI fails and refuses to update the baseline.
## Edge Cases & Boundary Handling

- **Canonical AST Normalization Pipeline**: Raw `ast.dump()` output is sensitive to Python AST runtime differences. The normalizer explicitly removes AST location metadata (`lineno`, `col_offset`, `end_lineno`, `end_col_offset`, `ctx`) and strips the leading docstring statement from function/class bodies before computing `CODE_FINGERPRINT`.
- **API vs TYPE Boundary**:
  - `API_FINGERPRINT` includes: parameter names, ordering, kind (positional-only `/`, positional-or-keyword, keyword-only `*`, `*args`, `**kwargs`), and literal default values (e.g. `timeout=30 → 60` triggers `API_FINGERPRINT` change).
  - `TYPE_FINGERPRINT` includes: raw type annotation expressions, generic subscriptions (`list[str]`), forward references, and return type annotations.
- **Dynamic f-string Exceptions**: When exception messages use dynamic expressions (`raise ValueError(f"Invalid {x}")`), `RAISE_DETAIL` normalizes the static string portions while ignoring dynamic variable evaluations.
- **Decorated Functions**: Standard decorators (`@property`, `@staticmethod`, `@classmethod`, `@lru_cache`) are tracked in `API_FINGERPRINT`. Custom/unknown decorators trigger `Unknown/Unclassified` review.
- **New-Symbol Gated Baseline Creation**: When a new symbol is introduced, baseline creation is **NOT automatic**. A baseline record is established only after the symbol passes all required documentation and type availability gates (Tier policy + `pydoclint` + `mypy`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST be housed as a standalone, portable Python package under `packages/pypypydocsync/`.
- **FR-002**: System MUST parse Python source files using Python's standard `ast` module through a canonical AST normalization pipeline (stripping location metadata and docstrings).
- **FR-003**: System MUST extract independent fingerprints for: `CODE`, `API`, `TYPE`, `DOC`, `RAISE_TYPE`, `RAISE_DETAIL`, and `EXAMPLE`.
- **FR-004**: System MUST maintain clear separation between `API_FINGERPRINT` (signature structure + default values) and `TYPE_FINGERPRINT` (annotations).
- **FR-005**: System MUST classify AST deltas into `High Impact`, `Candidate Low Impact`, and `Unknown/Unclassified`.
- **FR-006**: System MUST treat changes to default parameter values, literal constants/thresholds, exception types/details, and branching return paths as `High Impact`.
- **FR-007**: System MUST fail-safe all `Unknown/Unclassified` AST changes to a `Review Trigger`.
- **FR-008**: System MUST store baseline state modularly in `.project/pypypydocsync/<package>/<module>.json`.
- **FR-009**: System MUST allow baseline creation for newly added symbols ONLY after they satisfy all applicable quality, docstring, and type gates.
- **FR-010**: System MUST emit standardized, machine-readable `PYPYDOCSYNC001` failure reports during pytest guard runs.
- **FR-011**: System MUST provide a CLI command (`pypypydocsync accept`) requiring `--symbol` and `--reason` to acknowledge audited changes.
- **FR-012**: System MUST provide a synthetic fixture suite with at least 15 controlled edge cases (async, generators, decorators, `@property`, dataclasses, etc.).
- **FR-013**: System MUST collect empirical evaluation data (false positives, false negatives, classification accuracy) in an exportable PoC test report.

### Key Domain Entities

- **SymbolRepresentation**: Container holding the canonical AST nodes, location, and extracted fingerprints for a single Python function or method.
- **FingerprintSet**: The collection of discrete SHA-256 hashes (`code`, `api`, `types`, `doc`, `raise_type`, `raise_detail`, `example`) for a symbol.
- **ChangeClassification**: Enum (`LOW_IMPACT`, `HIGH_IMPACT`, `UNKNOWN`) resulting from evaluating the AST delta between working tree and baseline.
- **BaselineRecord**: Persisted JSON entity containing the verified fingerprint set, review status, timestamp, and audit reason.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Deterministic Fixture Execution)**: 100% of the 15 synthetic edge cases are parsed deterministically and produce the expected classification according to the versioned classifier rules. Any classification rule subsequently shown to be incorrect must be recorded as a PoC finding and used to revise the classifier.
- **SC-002 (Low False Positive Rate)**: Less than 10% false positive rate on candidate safe refactors (variable renames, pure structural rewrites) across the 20–50 PoC function suite.
- **SC-003 (Deterministic Behavioral Detection)**: 100% of defined behaviorally significant AST transformations in the PoC test set (defaults, thresholds, new raises, altered returns), when documentation remains unchanged, trigger `PYPYDOCSYNC001`.
- **SC-004 (Runtime Speed)**: Total execution time for scanning and verifying 50 functions is under 500 milliseconds.
- **SC-005 (Portability)**: The `packages/pypypydocsync/` folder can be copied to a clean, empty directory and successfully pass its own standalone test suite via `pytest`.

---

## Assumptions & Boundaries

- **Python Runtime**: Targets Python 3.12+ using standard library AST features (`ast.dump`, `ast.NodeVisitor`, `hashlib`).
- **Semantic Scope**: The system does not claim to mathematically prove the truth of natural-language prose; it enforces deterministic review obligations when code representations change.
- **Single-Package PoC**: Phase 1 focuses on single-function and method-level symbol synchronization. Transitive caller impact via CKG is explicitly scoped for Phase 2.
