# Tasks: 002-pypydocsync-adversarial-stress

**Input**: Design documents from `specs/002-pypydocsync-adversarial-stress/` (`spec.md`, `plan.md`)  
**Prerequisites**: `plan.md` (complete), `spec.md` (complete)  

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Associated User Story (`US1`, `US2`, `US3`)

---

## Phase 1: Test Infrastructure & Dual-Execution Engine

**Purpose**: Build controlled runtime behavioral comparison harness

- [x] T001 Initialize directory `packages/pypypydocsync/tests/adversarial/__init__.py`
- [x] T002 Implement dual-execution runtime harness in `packages/pypypydocsync/tests/adversarial/harness.py` (executes initial vs transformed snippet in isolated namespaces, capturing return values, exceptions, and side-effect traces without network/disk I/O)
- [x] T003 [P] Implement 10+ False-Negative adversarial cases (evaluation order, aliasing/identity, mutable defaults, closure mutations, generator early returns, boolean short-circuits) in `packages/pypypydocsync/tests/adversarial/cases.py`
- [x] T004 [P] Implement 5+ False-Positive adversarial cases (De Morgan equivalences, tuple unpacks, multi-line format equivalents) in `packages/pypypydocsync/tests/adversarial/cases.py`

---

## Phase 2: Behavioral Falsification & Baseline Evidence (Classifier v0.1)

**Purpose**: Run automated stress tests against frozen Classifier v0.1 and record raw evidence

- [x] T005 [US3] Implement automated test runner `packages/pypypydocsync/tests/adversarial/test_adversarial_stress.py` executing all 15+ cases
- [x] T006 [US3] Execute test harness against frozen Classifier v0.1 and generate initial falsification table (identifying potential false negatives and potential false positives under test inputs)

---

## Phase 3: Targeted Evolution to Classifier v0.2 / Limitation Documentation

**Purpose**: Refine classification rules or document fundamental AST limits

- [x] T007 Analyze root causes of discovered blind spots (e.g. statement reordering, aliasing, AST call sequence differences)
- [x] T008 Implement targeted rules or UNKNOWN fallbacks in `packages/pypypydocsync/pypydocsync/classifier.py` for v0.2
- [x] T009 Re-run all 22 original tests from `001-pypydocsync-core` to ensure zero regressions on baseline behavior

---

## Phase 4: Final Evaluation Report & Convergence

**Purpose**: Document all empirical findings and converge feature artifacts

- [x] T010 Generate final `specs/002-pypydocsync-adversarial-stress/adversarial_evaluation_report.md` comparing v0.1 vs v0.2 metrics and documenting known AST boundaries
- [x] T011 Run `/speckit-converge` and update `AGENTS.md` implemented ledger
