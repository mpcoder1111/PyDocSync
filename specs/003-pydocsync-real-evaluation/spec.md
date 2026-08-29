# Feature Specification: 003-pypydocsync-real-evaluation

## Real-Project Empirical Evaluation & Human Blind-Review Calibration for PyDocSync v0.2

**Feature Branch**: `003-pypydocsync-real-evaluation`  
**Created**: 2026-08-29  
**Last updated**: 2026-08-29  
**Status**: Draft  
**Input**: User description & Team review directive (Tri-part empirical calibration matrix)  

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Alignment with project constitution (Deterministic Platform, Quality Gates) |
| 2 | [User Scenarios & Testing](#user-scenarios--testing) | Empirical evaluation scenarios (US1: Real Production Symbol Baselining, US2: Realistic AI-Style Modifications, US3: Blind Human vs Classifier Concordance) |
| 3 | [Requirements](#requirements) | Functional requirements (FR-001 to FR-012) and evaluation protocol entities |
| 4 | [Success Criteria](#success-criteria) | Measurable empirical concordance, precision, recall, and runtime metrics |
| 5 | [Assumptions & Boundaries](#assumptions--boundaries) | Scope boundaries, blind evaluation rules, and frozen v0.2 constraints |

---

## Applicable Constitution Principles

*Per project governance (`.specify/memory/constitution.md`):*

| Principle | Applies? | Notes |
|---|---|---|
| **I. Two-Layer Pure Domain Architecture** | **YES** | Real-project evaluations test against production Layer-1 Logseq and PyDocSync toolkits. |
| **II. Spec-Driven Development (SDD)** | **YES** | Follows formal SDD lifecycle for Feature 003. |
| **III. Intent-First & Grounded Planning** | **YES** | Measures real-world correspondence to human developer judgment on realistic code changes. |
| **V. Deterministic Platform, AI-as-Producer** | **YES** | Tests AI-generated edits and assesses whether agents update docstrings appropriately or use acknowledgment. |
| **VI. Self-Enforcing Quality Gates** | **YES** | Validates `test_doc_sync_guard.py` across authentic multi-symbol packages. |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Production Codebase Baseline Initialization (Priority: P1)

As a repository maintainer or CI engineer, I want PyDocSync to scan real production modules in `packages/pypypydocsync/pypydocsync/` (and Layer-1 toolkits), verify docstring compliance, and generate modular `.project/pypypydocsync/` baseline lockfiles across 25+ real functions/methods, so that the codebase has an authentic starting synchronization baseline.

**Why this priority**: Necessary foundation for testing real modifications against authentic production code.

**Independent Test**: Run `pypypydocsync init` / baseline generator across production modules and confirm that all compliant public symbols are recorded into modular JSON files.

**Acceptance Scenarios**:
1. **Given** 25+ real production functions in `packages/pypypydocsync/pypydocsync/`, **When** the baseline is generated, **Then** `.project/pypypydocsync/packages/pypypydocsync/pypydocsync/*.json` lockfiles are created.
2. **Given** existing clean code, **When** `pypypydocsync check` runs, **Then** it reports 0 failures and passes.

---

### User Story 2 - Realistic AI-Generated Code Modifications (Priority: P1)

As an AI coding agent pair-programming on this repository, I want to execute realistic development modifications across 6 distinct categories (pure refactoring, bug fixes with threshold shifts, public API default tweaks, new exception paths, type annotation refinements, and docstring-only updates), so that we can evaluate PyDocSync's governance under realistic conditions.

**Why this priority**: Realistic AI modifications are the primary target workload for PyDocSync.

**Independent Test**: Apply 15+ realistic simulated code edits against baselined production symbols and record PyDocSync's response.

**Acceptance Scenarios**:
1. **Given** a pure internal refactor (e.g. list comprehension rewrite in a real function), **When** PyDocSync evaluates it, **Then** it produces `CANDIDATE_LOW_IMPACT` with `review_required=False`.
2. **Given** an altered default parameter or threshold in a real function, **When** PyDocSync evaluates it without a doc update, **Then** it triggers `PYPYDOCSYNC001` with `review_required=True` and actionable evidence.

---

### User Story 3 - Blind Human Assessment vs Classifier Concordance (Priority: P1)

As a researcher evaluating PyDocSync, I want each realistic code change assessed independently by human reviewers (without prior exposure to PyDocSync's prediction) answering two distinct questions:
1. **Q1**: *Does this change require documentation **REVIEW**? (Yes/No)*
2. **Q2**: *After review, does the documentation actually require an **UPDATE**? (Yes/No)*

so that we can measure real precision, recall, and false-alarm friction without confirmation bias, while distinguishing legitimate CLI acknowledgments from necessary docstring edits.

**Why this priority**: Establishes scientifically defensible alignment between PyDocSync and human engineering judgment as the primary ground-truth evaluation label.

**Independent Test**: Compare blind human review decisions with PyDocSync v0.2 predictions across all 15+ real-project cases, record inter-reviewer agreement (Reviewer A vs Reviewer B), and calculate concordance metrics.

**Acceptance Scenarios**:
1. **Given** 15+ realistic edits, **When** blind human decisions are compared against v0.2, **Then** a concordance matrix (`True Positive`, `True Negative`, `Conservative Over-Trigger`, `Unresolved Escape`) is computed.
2. **Given** an edit where doc is reviewed but remains accurate, **When** AI executes `pypypydocsync accept`, **Then** it is marked as a successful review acknowledgment rather than churn.

---

## Edge Cases & Boundary Handling

- **Primary Evaluation Label**: Blind human judgment is the primary evaluation label for review necessity; programmatic runtime execution serves as supporting empirical evidence.
- **Dual-Reviewer Protocol**: Two reviewers independently evaluate diffs (presented only with `git diff` of code + docstring). Disagreements are flagged as `DISPUTED` and reconciled.
- **Unnecessary Churn Tracking**: When an agent edits a docstring for a change where human review confirmed the existing doc was already accurate, the action is categorized as `UNNECESSARY_CHURN`.
- **Frozen Classifier v0.2**: Classifier v0.2 logic remains 100% frozen during the entire evaluation experiment.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST establish distributed JSON baselines for 25+ real production symbols in `packages/pypypydocsync/pypydocsync/`.
- **FR-002**: System MUST define a benchmark of at least 15 realistic AI-style code modifications across 6 categories (refactors, bug fixes, threshold shifts, API default tweaks, exception additions, doc updates).
- **FR-003**: System MUST execute frozen Classifier v0.2 against all 15+ realistic transformations.
- **FR-004**: System MUST record independent, blind human review assessments capturing both Q1 (Review Required) and Q2 (Update Required) with dual-reviewer concordance.
- **FR-005**: System MUST record AI-agent remediation behavior (doc update vs `pypypydocsync accept` vs unnecessary churn).
- **FR-006**: System MUST generate an empirical Tri-Part Concordance Table in `specs/003-pypydocsync-real-evaluation/real_evaluation_report.md`.
- **FR-007**: System MUST compute and publish observed Precision, Recall, Over-Trigger, and Unnecessary Documentation Churn metrics.
- **FR-008**: System MUST verify that total scan and check time across the entire production package remains under 200 ms.
- **FR-009**: All 38 previous automated tests (22 core + 16 adversarial) MUST continue to pass 100%.

### Key Domain Entities

- **RealProjectScenario**: Model holding target production symbol, code modification diff, modification category, and rationale.
- **HumanAssessmentRecord**: Structure holding Reviewer A (Q1, Q2), Reviewer B (Q1, Q2), and Consensus (Review Required, Update Required).
- **TriPartEvaluationRecord**: Structure recording:
  1. `pypydocsync_v02_prediction` (`Impact`, `RuleResult`, `review_required`)
  2. `human_consensus` (`review_required: bool`, `update_required: bool`)
  3. `runtime_behavior_changed` (`True` / `False`)
  4. `ai_agent_remediation` (`DOC_UPDATED` / `CLI_ACCEPTED` / `UNNECESSARY_CHURN`)
  5. `concordance_verdict` (`CONCORDANT_REVIEW`, `CONCORDANT_PASS`, `CONSERVATIVE_OVER_TRIGGER`, `UNRESOLVED_ESCAPE`)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Real Symbol Coverage)**: Minimum of 25 real production symbols baselined and 15 realistic AI-style modifications evaluated.
- **SC-002 (Empirical Evaluation Reporting)**: Complete observed Precision, Recall, and Over-Trigger metrics reported against primary blind human consensus.
- **SC-003 (Low Unnecessary Churn)**: ≤ 10% Unnecessary Documentation Churn Rate by AI agents across the benchmark suite.
- **SC-004 (Clean AI-Agent Governance)**: 100% of review obligations successfully resolved by AI agents using appropriate doc updates or explicit CLI acceptances.
- **SC-005 (Execution Speed)**: Total scan and verification of the full production suite executes in under 200 milliseconds.


---

## Assumptions & Boundaries

- **Target Package**: Evaluates the real, shipped `packages/pypypydocsync/pypydocsync/` modules (`ast_extract.py`, `fingerprint.py`, `classifier.py`, `baseline.py`, `report.py`, `cli.py`).
- **Frozen Logic**: Classifier v0.2 code is frozen; no rule tweaks are made during evaluation.
