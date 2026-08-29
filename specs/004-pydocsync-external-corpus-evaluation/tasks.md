# Tasks: 004-pypydocsync-external-corpus-evaluation

**Input**: Design documents from `specs/004-pypydocsync-external-corpus-evaluation/` (`spec.md`, `plan.md`)  
**Prerequisites**: `plan.md` (complete), `spec.md` (complete)  

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Associated User Story (`US1`, `US2`, `US3`)

---

## Phase 1: Multi-Repository Manifest & Corpus Ingestion (Priority: P1)

**Purpose**: Establish reproducible, Apache-2.0 licensed external test corpus

- [x] T001 [US1] Create directory `packages/pypypydocsync/tests/external_evaluation/` and `corpus_manifest.json` referencing Dulwich, Janome, and python-sdb with pinned commits and licenses
- [x] T002 [US1] Ingest representative modules into `packages/pypypydocsync/tests/external_evaluation/corpus/` (`dulwich_pack.py`, `janome_tokenizer.py`, `sdb_struct.py`) and initialize baseline lockfiles for 60+ external symbols

---

## Phase 2: Cross-Repository Scenarios & Blind Review Dataset (Priority: P1)

**Purpose**: Author 20+ realistic AI modifications across the 3 external codebases and record blind human consensus

- [x] T003 [P] [US2] Author 20+ realistic AI development scenarios in `packages/pypypydocsync/tests/external_evaluation/scenarios.py` across Dulwich, Janome, and python-sdb covering all 6 categories
- [x] T004 [P] [US3] Record independent blind human review judgments in `packages/pypypydocsync/tests/external_evaluation/human_assessments.py` (Reviewer A & B assessing Q1 Review and Q2 Update)

---

## Phase 3: Automated Generalization Evaluation & Profiling (Priority: P1)

**Purpose**: Run automated cross-repository evaluation against frozen PyDocSync v0.2

- [x] T005 [US3] Implement automated test runner `packages/pypypydocsync/tests/external_evaluation/test_external_evaluation.py`
- [x] T006 [US3] Measure cross-repository Recall, Precision, Over-Trigger rate, and Churn rate across the 20+ external scenarios
- [x] T007 [US3] Profile external corpus scanning speed (< 200 ms target)
- [x] T008 Re-run all 54 existing tests (22 core + 16 adversarial + 16 real-evaluation) to ensure zero regressions

---

## Phase 4: Final Generalization Report & Convergence

**Purpose**: Document multi-repository findings and converge feature artifacts

- [x] T009 [US3] Generate comprehensive `specs/004-pypydocsync-external-corpus-evaluation/external_evaluation_report.md` with per-repository metrics breakdown
- [x] T010 Run `/speckit-converge` and update `AGENTS.md` implemented ledger
