# Feature Specification: 004-pypydocsync-external-corpus-evaluation

## Multi-Repository Generalization Benchmark for PyDocSync v0.2 across Diverse Apache-2.0 Python Projects

**Feature Branch**: `004-pypydocsync-external-corpus-evaluation`  
**Created**: 2026-08-29  
**Last updated**: 2026-08-29  
**Status**: Draft  
**Input**: User description & Team review directive (External Multi-Repository Generalization)  

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Alignment with project constitution (Deterministic Platform, Quality Gates) |
| 2 | [User Scenarios & Testing](#user-scenarios--testing) | Empirical generalization scenarios across 3 distinct Apache-2.0 Python repositories |
| 3 | [Requirements](#requirements) | Functional requirements (FR-001 to FR-012) and evaluation protocol entities |
| 4 | [Success Criteria](#success-criteria) | Generalization recall, precision, and reproducibility targets |
| 5 | [Assumptions & Boundaries](#assumptions--boundaries) | Read-only external source corpus, pinned commit manifests, frozen v0.2 rules |

---

## Applicable Constitution Principles

*Per project governance (`.specify/memory/constitution.md`):*

| Principle | Applies? | Notes |
|---|---|---|
| **I. Two-Layer Pure Domain Architecture** | **YES** | Evaluation engine and external benchmarks operate in pure Python with clean Layer-1 contracts. |
| **II. Spec-Driven Development (SDD)** | **YES** | Follows formal SDD lifecycle for Feature 004. |
| **III. Intent-First & Grounded Planning** | **YES** | Evaluates whether PyDocSync generalizes across diverse external coding styles without per-project tuning. |
| **V. Deterministic Platform, AI-as-Producer** | **YES** | Tests AI-style modifications against third-party open-source codebases. |
| **VI. Self-Enforcing Quality Gates** | **YES** | Preserves 100% pass rates across previous 54 automated tests. |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Repository Corpus Manifest & Read-Only Ingestion (Priority: P1)

As a researcher or system auditor, I want a reproducible corpus manifest (`corpus_manifest.json`) referencing 3 distinct, permissively licensed (Apache-2.0) pure-Python open-source repositories with pinned commit SHAs, license notices, and symbol extractors, so that the external corpus can be baselined deterministically without modifying upstream source code or violating licenses.

**Why this priority**: Foundational for reproducible, legally clean multi-repo generalization testing.

**Target Corpus (3 Distinct Repositories)**:
1. **Repository A (Dulwich - Pure-Python Git & Network Engine)**: Data structures, file parsing, protocol exceptions, default parameters (`jelmer/dulwich@v0.21.7`).
2. **Repository B (Janome - Pure-Python Japanese Morphological Parser)**: Heavy algorithmic logic, tokenization, dict/trie lookups, dictionary defaults (`mocobeta/janome@v0.5.0`).
3. **Repository C (python-sdb - Pure-Python Binary Structure Unpacking Engine)**: Bitwise operations, packing thresholds, binary struct unpack checks, custom errors (`williballenthin/python-sdb@v0.1.0`).

**Independent Test**: Parse modules from the 3 corpora, verify license integrity, extract 20+ symbols per project (60+ total symbols), and generate isolated baseline lockfiles.

**Acceptance Scenarios**:
1. **Given** 3 external Apache-2.0 pure-Python libraries, **When** ingested via the corpus manifest, **Then** all 60+ symbols are extracted and baselined into `packages/pypypydocsync/tests/external_evaluation/corpus/`.
2. **Given** clean upstream files, **When** PyDocSync checks them, **Then** all 3 projects report 0 synchronization failures against initial baseline.

---

### User Story 2 - Realistic AI Modifications Across External Projects (Priority: P1)

As an AI coding agent or maintainer, I want to evaluate 20+ realistic development modifications across the 3 external codebases (covering refactoring, bug fixes, threshold shifts, API default tweaks, exception additions, and doc updates), so that we can test PyDocSync v0.2 against previously unseen Python coding styles without project-specific classifier tuning.

**Why this priority**: The ultimate test of generalizability for an AI-agent governance tool.

**Independent Test**: Execute frozen Classifier v0.2 across all 20+ external scenarios and record its classifications; compare predictions independently against blind human review consensus.

**Acceptance Scenarios**:
1. **Given** a realistic code modification in an external repository, **When** evaluated, **Then** frozen PyDocSync v0.2 classifies the change and emits structured evidence without project-specific configuration.
2. **Given** the classification, **When** compared against blind human review consensus, **Then** the empirical concordance verdict is recorded.

---

### User Story 3 - Generalization Tri-Part Evaluation & Escalation Rate Measurement (Priority: P1)

As a researcher evaluating PyDocSync, I want each external modification assessed with dual-reviewer blind human consensus (Reviewer A & Reviewer B, assessing Q1 Review Required and Q2 Update Required without seeing PyDocSync output), runtime behavior tests, and AI remediation actions, so that we can report empirical generalization Precision, Recall, Over-Trigger, Churn, and UNKNOWN/Escalation rates across external codebases.

**Why this priority**: Eliminates author bias and provides defensible empirical evidence for public release.

**Independent Test**: Execute `pytest packages/pypypydocsync/tests/external_evaluation/` and generate the multi-repository report.

**Acceptance Scenarios**:
1. **Given** 20+ external scenarios, **When** blind human decisions are compared against v0.2, **Then** the multi-repo concordance matrix and UNKNOWN/escalation rate are computed and published.

---

## Edge Cases & Boundary Handling

- **Read-Only External Code**: Upstream projects remain completely unmodified; test fixtures and synthetic mutations live in `packages/pypypydocsync/tests/external_evaluation/`.
- **Frozen Classifier v0.2**: Classifier v0.2 logic remains 100% frozen during the entire multi-repo experiment. No per-project rule branches or tuning permitted.
- **Reproducible Corpus Manifest**: Pinned commit SHAs, license notices, and symbol extractors documented in `corpus_manifest.json`.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create `packages/pypypydocsync/tests/external_evaluation/` with `corpus_manifest.json` referencing 3 distinct Apache-2.0 pure-Python open-source libraries (Dulwich, Janome, python-sdb).
- **FR-002**: System MUST baseline at least 20 symbols from each project (≥ 60 total external symbols).
- **FR-003**: System MUST define at least 20 realistic AI-style modification scenarios across the 3 external projects covering all 6 development categories.
- **FR-004**: System MUST execute frozen Classifier v0.2 against all 20+ external scenarios without per-project customizations.
- **FR-005**: System MUST record independent blind human consensus judgments (Reviewer A & Reviewer B, assessing Q1 Review Required and Q2 Update Required without seeing PyDocSync predictions).
- **FR-006**: System MUST track AI agent remediation behavior (`DOC_UPDATED`, `CLI_ACCEPTED`, `UNNECESSARY_CHURN`).
- **FR-007**: System MUST generate an empirical Multi-Repository Generalization Report under `specs/004-pypydocsync-external-corpus-evaluation/external_evaluation_report.md`.
- **FR-008**: System MUST compute and report observed Recall, Precision, Over-Trigger rate, Unnecessary Churn rate, and UNKNOWN/Escalation rate scoped to the evaluated scenarios.
- **FR-009**: System MUST verify that scanning all external symbols executes in under 200 ms.
- **FR-010**: All 54 previous automated tests MUST continue to pass 100%.

### Key Domain Entities

- **ExternalCorpusManifest**: Metadata entity capturing repository name, upstream URL, commit SHA, license type, and target module list.
- **ExternalScenarioRecord**: Structure holding project name, target symbol, code modification diff, and category.
- **MultiRepoConcordanceResult**: Structure holding PyDocSync prediction, human consensus, AI remediation, concordance category, and escalation status.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Corpus Diversity & Scale)**: 3 distinct Apache-2.0 Python repositories, ≥ 60 external symbols baselined, and ≥ 20 realistic scenarios evaluated.
- **SC-002 (Empirical Generalization Reporting)**: Complete observed Recall, Precision, Over-Trigger rate, and UNKNOWN/Escalation rate reported for the external benchmark, scoped to evaluated scenarios.
- **SC-003 (Low Unnecessary Churn)**: ≤ 10% Unnecessary Documentation Churn Rate across external scenarios.
- **SC-004 (Reproducible Manifest)**: 100% reproducible benchmark definition in `corpus_manifest.json`.
- **SC-005 (Execution Speed)**: Total scan across all external projects completes in under 200 ms.


---

## Assumptions & Boundaries

- **Pure Python Focus**: External libraries must be pure Python 3.10+ without C-extensions.
- **Apache-2.0 Licensing**: Only permissively licensed Apache-2.0 or MIT/BSD code used for evaluation fixtures.
