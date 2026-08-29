# Tasks: 001-pypydocsync-core

**Input**: Design documents from `specs/001-pypydocsync-core/` (`spec.md`, `plan.md`)  
**Prerequisites**: `plan.md` (complete), `spec.md` (complete)  

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Associated User Story (`US1`, `US2`, `US3`, `US4`)

---

## Phase 1: Setup & Shared Infrastructure

**Purpose**: Package scaffold and test fixtures

- [x] T001 Initialize package directory `packages/pypypydocsync/` with `pyproject.toml` and `README.md`
- [x] T002 Create package module layout `packages/pypypydocsync/pypydocsync/__init__.py` and exports
- [x] T003 Create 15 synthetic edge-case fixtures in `packages/pypypydocsync/tests/fixtures/synthetic_cases.py` (covering async, decorators, `@property`, generators, `@overload`, dataclasses, default arguments, nested functions, lambdas, and exception message alterations)

---

## Phase 2: User Story 1 — Deterministic Representation Fingerprinting (Priority: P1)

**Purpose**: Core AST extraction and discrete fingerprint generation

- [x] T004 [US1] Implement canonical AST normalization pipeline in `packages/pypypydocsync/pypydocsync/ast_extract.py` (stripping location metadata and docstrings)
- [x] T005 [P] [US1] Implement `API_FINGERPRINT` and `TYPE_FINGERPRINT` extractors in `packages/pypypydocsync/pypydocsync/fingerprint.py` (isolating default values in API and annotations in TYPE)
- [x] T006 [P] [US1] Implement `RAISE_TYPE` and `RAISE_DETAIL` extractors in `packages/pypypydocsync/pypydocsync/fingerprint.py`
- [x] T007 [US1] Implement `DOC_FINGERPRINT` and `EXAMPLE_FINGERPRINT` extractors in `packages/pypypydocsync/pypydocsync/fingerprint.py`
- [x] T008 [US1] Build Layer 1 unit test suite `packages/pypypydocsync/tests/test_fingerprint.py` verifying AST normalization and all 7 discrete fingerprints

---

## Phase 3: User Story 2 — AST Change Impact Classification (Priority: P1)

**Purpose**: Classify AST deltas into High Impact, Candidate Low Impact, and Unknown using an extensible rule engine

- [x] T009 [US2] Implement extensible rule-based classifier architecture in `packages/pypypydocsync/pypydocsync/classifier.py` returning `RuleResult(classification, rule_id, evidence, reason)`
- [x] T010 [US2] Implement High-Impact rules (default arg changes, literal thresholds, exception type/detail, branching return paths) in `packages/pypypydocsync/pypydocsync/classifier.py`
- [x] T011 [US2] Implement Candidate Low-Impact rules (variable renames, loop-to-comp, helper extract) in `packages/pypypydocsync/pypydocsync/classifier.py`
- [x] T012 [US2] Implement Unknown/Unclassified fallback rule to Review Trigger in `packages/pypypydocsync/pypydocsync/classifier.py`
- [x] T013 [US2] Build Layer 2 unit test suite `packages/pypypydocsync/tests/test_classifier.py` testing against all 15 synthetic fixture cases and verifying structured evidence payloads

---

## Phase 4: User Story 3 — Distributed Baseline Management & Machine-Readable Output (Priority: P2)

**Purpose**: Modular JSON lockfiles and `PYPYDOCSYNC001` test feedback

- [x] T014 [US3] Implement modular baseline persistence engine in `packages/pypypydocsync/pypydocsync/baseline.py` (`.project/pypypydocsync/<pkg>/<mod>.json`)
- [x] T015 [US3] Implement gated baseline creation rule in `packages/pypypydocsync/pypydocsync/baseline.py` (disallowing baseline creation for symbols with missing/failing docs)
- [x] T016 [US3] Implement `PYPYDOCSYNC001` structured error report formatter in `packages/pypypydocsync/pypydocsync/report.py` (including evidence and remediation commands)
- [x] T017 [US3] Build Layer 3 integration test suite `packages/pypypydocsync/tests/test_integration.py` verifying distributed baseline saving, loading, and gated creation

---

## Phase 5: User Story 4 — Explicit CLI Review Acknowledgment & Guard Integration (Priority: P2)

**Purpose**: `pypypydocsync accept` CLI command and pytest commit guard

- [x] T018 [US4] Implement CLI entrypoint in `packages/pypypydocsync/pypydocsync/cli.py` (`pypypydocsync accept --symbol ... --reason "..."`, `pypypydocsync check`, `pypypydocsync init`)
- [x] T019 [US4] Implement project commit guard `tests/guards/test_doc_sync.py` integrating PyDocSync into repository pytest runs
- [x] T020 [US4] Build Layer 4 AI agent workflow test suite `packages/pypypydocsync/tests/test_agent_workflow.py` simulating the full loop: `AI change → pytest FAIL (PYPYDOCSYNC001) → CLI accept / doc update → pytest PASS`

---

## Phase 6: Empirical Evaluation & PoC Report

**Purpose**: Measure real-world false-positive and false-negative metrics with stage-by-stage profiling

- [x] T021 Run PyDocSync scanner and classifier across 20–50 real functions in `logseq_toolkit/` and synthetic cases
- [x] T022 Populate Empirical Evidence Collection Table (`specs/001-pypydocsync-core/poc_evaluation_report.md`) recording all transformation results, false-positive/negative findings, and stage-by-stage timing (Parse, Fingerprint, Classify, I/O)
