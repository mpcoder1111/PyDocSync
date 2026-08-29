# Tasks: 003-pypydocsync-real-evaluation

**Input**: Design documents from `specs/003-pypydocsync-real-evaluation/` (`spec.md`, `plan.md`)  
**Prerequisites**: `plan.md` (complete), `spec.md` (complete)  

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Associated User Story (`US1`, `US2`, `US3`)

---

## Phase 1: Production Baseline Initialization (Priority: P1)

**Purpose**: Establish authentic lockfiles for real production code

- [x] T001 [US1] Initialize baseline lockfiles under `.project/pypypydocsync/packages/pypypydocsync/pypydocsync/` for all 6 production modules (25+ symbols)
- [x] T002 [US1] Run `pypypydocsync check` and verify 100% clean baseline pass across the repository

---

## Phase 2: Realistic AI Modification Benchmark & Blind Review Dataset (Priority: P1)

**Purpose**: Author realistic AI-style development scenarios and collect blind human assessments

- [x] T003 [P] [US2] Author 15+ realistic development transformation scenarios in `packages/pypypydocsync/tests/real_evaluation/scenarios.py` across 6 categories (refactors, bug fixes, threshold shifts, API default tweaks, exception additions, type contract changes, doc updates)
- [x] T004 [P] [US3] Record independent blind human review judgments in `packages/pypypydocsync/tests/real_evaluation/human_assessments.py` without exposure to PyDocSync classifier outputs

---

## Phase 3: Tri-Part Concordance Engine & Profiling (Priority: P1)

**Purpose**: Automated evaluation comparing PyDocSync v0.2, runtime behavior, and blind human judgment

- [x] T005 [US3] Implement automated tri-part evaluation runner in `packages/pypypydocsync/tests/real_evaluation/test_real_evaluation.py`
- [x] T006 [US3] Measure empirical Recall, Precision, and Conservative Over-Trigger rates across the 15+ real-project scenarios
- [x] T007 [US3] Profile full-project scanning speed across all real modules (< 200 ms target)
- [x] T008 Re-run all 38 regression tests (22 core + 16 adversarial) to verify zero system regressions

---

## Phase 4: Final Evaluation Report & Convergence

**Purpose**: Document all empirical metrics and converge feature artifacts

- [x] T009 [US3] Generate comprehensive `specs/003-pypydocsync-real-evaluation/real_evaluation_report.md` with Tri-Part Concordance Matrix and AI governance observations
- [x] T010 Run `/speckit-converge` and update `AGENTS.md` implemented ledger
