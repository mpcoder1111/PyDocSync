# Implementation Plan: 003-pypydocsync-real-evaluation

**Branch**: `003-pypydocsync-real-evaluation` | **Date**: 2026-08-29 | **Spec**: [`specs/003-pypydocsync-real-evaluation/spec.md`](spec.md)  
**Input**: Feature specification from `specs/003-pypydocsync-real-evaluation/spec.md`  

---

## Summary

Conduct a rigorous real-project empirical evaluation of frozen PyDocSync v0.2 across production codebase modules. Establish initial baseline lockfiles for 25+ real functions/methods, apply 15+ realistic AI-style code modifications across 6 development categories, gather independent blind human review judgments, and evaluate the tri-part concordance matrix (PyDocSync prediction vs Runtime behavior vs Blind human judgment vs AI-agent remediation).

---

## Technical Context

- **Target Corpus**: Real production modules under `packages/pypypydocsync/pypydocsync/` (`ast_extract.py`, `fingerprint.py`, `classifier.py`, `baseline.py`, `report.py`, `cli.py`).
- **Baseline Storage**: Modular JSON files in `.project/pypypydocsync/packages/pypypydocsync/pypydocsync/*.json`.
- **Evaluation Matrix Engine**: Dedicated empirical test suite in `packages/pypypydocsync/tests/real_evaluation/`.
- **Methodology**: Tri-part comparison:
  1. `PyDocSync v0.2 Prediction` (Impact, RuleResult, review_required)
  2. `Programmatic Runtime Behavior` (pytest suite execution)
  3. `Blind Human Review Assessment` (Independent evaluation without seeing PyDocSync output)
  4. `AI-Agent Response` (Doc update vs CLI accept vs invalid churn)
- **Reporting**: Automated report generator outputting to `specs/003-pypydocsync-real-evaluation/real_evaluation_report.md`.

---

## Constitution Check

*Constitution: `.specify/memory/constitution.md` | Standards: `.specify/memory/standards/`*

| Gate | Principle | Status | Notes |
|---|---|---|---|
| Does this feature keep business logic pure Python with zero framework coupling? | I. Two-Layer Architecture | **YES** | Evaluation engine and baselines operate in pure Python. |
| Is a `spec.md` present and complete before this plan was written? | II. Spec-Driven Development | **YES** | `specs/003-pypydocsync-real-evaluation/spec.md` created. |
| Does the evaluation eliminate human confirmation bias? | III. Intent-First / Test Discipline | **YES** | Enforces blind human review protocol before comparison. |
| Is Classifier v0.2 kept frozen during evaluation? | V. Deterministic Platform | **YES** | No mid-flight heuristic tweaks allowed. |

---

## Project Structure & File Layout

```text
packages/pypypydocsync/
├── pypydocsync/                           # Real production modules (Target of evaluation)
│   ├── ast_extract.py
│   ├── fingerprint.py
│   ├── classifier.py                  # Frozen v0.2
│   ├── baseline.py
│   ├── report.py
│   └── cli.py
├── tests/
│   ├── test_fingerprint.py            # Core Layer 1
│   ├── test_classifier.py             # Core Layer 2
│   ├── test_integration.py            # Core Layer 3
│   ├── test_agent_workflow.py         # Core Layer 4
│   ├── adversarial/                   # Feature 002 adversarial suite
│   └── real_evaluation/               # Feature 003 real-project evaluation
│       ├── __init__.py
│       ├── scenarios.py               # 15+ realistic AI-style code modification diffs
│       ├── human_assessments.py       # Blind human review dataset (recorded independently)
│       └── test_real_evaluation.py    # Automated tri-part concordance test & report generator

.project/pypypydocsync/packages/pypypydocsync/pypydocsync/ # Baselined production lockfiles
├── ast_extract.json
├── fingerprint.json
├── classifier.json
├── baseline.json
├── report.json
└── cli.json

specs/003-pypydocsync-real-evaluation/
├── spec.md                            # Specification
├── plan.md                            # This file
├── tasks.md                           # Dependency-ordered tasks
└── real_evaluation_report.md          # Final empirical concordance & precision/recall report
```

---

## Execution Workflow & Roadmap

1. **Phase 1 (Baseline Initialization)**:
   - Run baseline lockfile generator across all 6 production modules in `packages/pypypydocsync/pypydocsync/`.
   - Verify `pypypydocsync check` passes cleanly with 0 failures on initial clean codebase.
2. **Phase 2 (Realistic AI Modification Benchmark & Blind Review)**:
   - Author 15+ realistic code modifications spanning the 6 categories in `scenarios.py`.
   - Record independent blind human assessments in `human_assessments.py`.
3. **Phase 3 (Tri-Part Automated Evaluation & Profiling)**:
   - Implement `test_real_evaluation.py` to evaluate each scenario against PyDocSync v0.2, test runner, and blind human data.
   - Profile full-package scan time.
4. **Phase 4 (Final Concordance Report & Convergence)**:
   - Compute Precision, Recall, and Over-Trigger metrics.
   - Generate `real_evaluation_report.md`.
   - Run `/speckit-converge`.
