# Feature Specification: 002-pypydocsync-adversarial-stress

## Adversarial Stress Testing & Behavioral Falsification for PyDocSync Classifier

**Feature Branch**: `002-pypydocsync-adversarial-stress`  
**Created**: 2026-08-29  
**Last updated**: 2026-08-29  
**Status**: Draft  
**Input**: User description & Team review directive (Falsification matrix)  

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Alignment with project constitution (Deterministic Platform, Quality Gates) |
| 2 | [User Scenarios & Testing](#user-scenarios--testing) | Adversarial test journeys (US1: False-Negative Attacks, US2: False-Positive Attacks, US3: Dual-Execution Behavioral Falsification) |
| 3 | [Requirements](#requirements) | Functional requirements (FR-001 to FR-010) and test harness entities |
| 4 | [Success Criteria](#success-criteria) | Measurable falsification targets and empirical recording criteria |
| 5 | [Assumptions & Boundaries](#assumptions--boundaries) | Scope boundaries, execution isolation, and versioning rules |

---

## Applicable Constitution Principles

*Per project governance (`.specify/memory/constitution.md`):*

| Principle | Applies? | Notes |
|---|---|---|
| **I. Two-Layer Pure Domain Architecture** | **YES** | Test fixtures and execution harness live inside `packages/pypypydocsync/tests/adversarial/` with zero web coupling. |
| **II. Spec-Driven Development (SDD)** | **YES** | Follows formal SDD lifecycle for Feature 002. Immutable historical record of 001 preserved. |
| **III. Intent-First & Grounded Planning** | **YES** | Directly attacks classifier hypotheses to find blind spots before public release. |
| **V. Deterministic Platform, AI-as-Producer** | **YES** | Evaluates deterministic AST transformations against programmatic ground truth. |
| **VI. Self-Enforcing Quality Gates** | **YES** | Discovered blind spots become permanent regression fixtures. |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - False-Negative Adversarial Attacks ("Dangerous but Looks Safe") (Priority: P1)

As a researcher or system auditor, I want to submit code transformations where internal variable names or local structures appear benign to standard AST diffing but actually alter program semantics (e.g. evaluation order, mutable side-effects, closure variable capture, generator early termination, short-circuiting, aliasing / object-identity shifts), so that we can identify and measure any potential silent escapes in Classifier v0.1.

**Why this priority**: Highest safety risk. A false negative means an AI agent introduces a breaking behavioral change that bypasses review.

**Independent Test**: Execute the dual-execution harness on 10+ false-negative adversarial snippets, verifying that empirical runtime behavioral differences under defined test inputs are captured and compared against the classifier's verdict.

**Acceptance Scenarios**:
1. **Given** an evaluation-order shift (e.g. `f(a()) + g(b())` → `g(b()) + f(a())` with side-effects in `a()` and `b()`), **When** evaluated, **Then** the test harness detects runtime execution divergence under defined test inputs and records the classifier's response.
2. **Given** an aliasing vs copy shift (`a = b` vs `a = list(b)`), **When** evaluated, **Then** the harness detects caller-side mutation state divergence.
3. **Given** a closure variable capture mutation, **When** evaluated, **Then** the harness detects divergent return states from the generated callable.

---

### User Story 2 - False-Positive Adversarial Attacks ("Safe but Looks Dangerous") (Priority: P1)

As a developer or AI agent, I want to submit complex but strictly equivalent refactorings (e.g. equivalent boolean logic rewrites, multi-variable tuple unpacking, advanced nested comprehension equivalents), so that we can determine whether the classifier triggers unnecessary review friction on safe code.

**Why this priority**: High developer friction risk. Excessive over-triggering causes alert fatigue.

**Independent Test**: Execute 5+ complex refactor transformations through runtime behavior verification and confirm empirical behavioral equivalence under defined test inputs.

**Acceptance Scenarios**:
1. **Given** a De Morgan's boolean transformation (`not (a and b)` → `(not a) or (not b)`), **When** evaluated, **Then** runtime behavior is confirmed identical under test inputs and classifier impact is measured.
2. **Given** a safe multi-variable tuple swap (`a, b = b, a`), **When** evaluated, **Then** runtime behavior is confirmed identical under test inputs.

---

### User Story 3 - Dual-Execution Behavioral Evidence Harness (Priority: P1)

As an engineer evaluating the classifier, I want an automated test harness that executes both the original snippet and transformed snippet against controlled test inputs, captures observed output/side-effect deltas, and automatically flags potential false negatives (`Runtime Differed && Classifier == LOW`) and potential false positives (`Runtime Identical && Classifier == HIGH`), so that classifications are judged against programmatic execution evidence.

**Why this priority**: Eliminates human labeling bias by providing empirical runtime execution evidence.

**Independent Test**: Run `pytest packages/pypypydocsync/tests/adversarial/` and generate the automated comparison matrix.

**Acceptance Scenarios**:
1. **Given** any adversarial snippet, **When** the harness runs, **Then** it executes both variants in isolated scope and records `(runtime_equal, classifier_label, verdict_type)`.

---

## Edge Cases & Boundary Handling

- **Controlled In-Process Execution**: Fixtures are strictly prohibited from performing network I/O, disk filesystem access, subprocess spawning, OS system calls, threading, or unbounded loops.
- **Side-Effect Capture**: Harness captures returned objects, raised exception types/messages, and call-order trace lists to detect non-return side effects.
- **Fail-Safe Limitation Rule**: If a subtle semantic change cannot be deterministically resolved by pure AST analysis, the classifier MUST classify as `UNKNOWN` (review trigger) and document the behavior as an AST static-analysis boundary limitation rather than guessing.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Test suite MUST live under `packages/pypypydocsync/tests/adversarial/`.
- **FR-002**: System MUST define at least 15 adversarial test cases across two primary matrices: False-Negative Attacks (10+, including aliasing/identity) and False-Positive Attacks (5+).
- **FR-003**: Harness MUST execute both initial and transformed code variants against defined test inputs to establish empirical runtime evidence.
- **FR-004**: Harness MUST capture return values, exception types/messages, and call-order side effects.
- **FR-005**: Harness MUST record every result into an exportable matrix: `(case_id, runtime_behavior_changed, classifier_v01_label, potential_verdict, evidence)`.
- **FR-006**: Transformations where runtime behavior differs under test inputs but Classifier v0.1 predicts `LOW_IMPACT` MUST be categorized as `POTENTIAL_FALSE_NEGATIVE`.
- **FR-007**: Transformations where runtime behavior is identical under test inputs but Classifier v0.1 predicts `HIGH_IMPACT` MUST be categorized as `POTENTIAL_FALSE_POSITIVE`.
- **FR-008**: Classifier v0.1 codebase MUST remain frozen during the initial evaluation run to record unbiased baseline evidence.
- **FR-009**: Justified rule refinements MUST be implemented incrementally as Classifier v0.2, retaining v0.1 comparison fixtures. Unresolvable dynamic semantics must safely route to `UNKNOWN`.
- **FR-010**: Final results MUST be synthesized into an updated adversarial findings report under `specs/002-pypydocsync-adversarial-stress/adversarial_evaluation_report.md`.

### Key Domain Entities

- **AdversarialSnippet**: Structure holding initial code, transformed code, sample inputs, and expected runtime behavioral delta.
- **RuntimeExecutionResult**: Captured return value, raised exception, and execution order trace.
- **PotentialFalsificationVerdict**: Enum (`MATCH_HIGH`, `MATCH_LOW`, `SAFE_UNKNOWN_FALLBACK`, `POTENTIAL_FALSE_NEGATIVE`, `POTENTIAL_FALSE_POSITIVE`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Adversarial Coverage)**: Minimum of 15 distinct adversarial transformations (including evaluation order, aliasing/identity, mutable defaults, closure mutations, generator semantics) executed through the dual-execution harness.
- **SC-002 (Empirical Runtime Evidence)**: 100% of adversarial fixtures execute in under 1 second total with deterministic runtime verification under defined inputs.
- **SC-003 (Empirical Evidence Logging)**: Complete tabular breakdown of all discovered potential false positives, false negatives, and rule weaknesses generated.
- **SC-004 (Targeted v0.2 Evolution)**: Any discovered blind spot is either (a) resolved via a verified v0.2 rule refinement without causing regressions, or (b) formally documented as a known fundamental AST limitation in the evaluation report with an `UNKNOWN` fallback.
- **SC-005 (Zero Regressions on Core)**: All 22 original test cases from `001-pypydocsync-core` continue to pass 100% on any v0.2 updates.


---

## Assumptions & Boundaries

- **Local Scope**: Adversarial stress testing focuses on intra-function transformations; call-graph transitive propagation remains in Phase 3.
- **Isolation**: Executions run in-memory within the test runner process using controlled namespaces.
