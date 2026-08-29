# PyDocSync: Deterministic Representation Synchronization for AI-Assisted Codebases

## Research Overview & System Whitepaper / RFC Draft

**Project**: PyDocSync (`packages/pypydocsync`)  
**Version**: `0.2.0 (Frozen Research Prototype)`  
**Status**: Shipped & Empirically Evaluated (Features 001, 002, 003)  
**Date**: 2026-08-29  

---

## 1. The Core Problem: The Code-Documentation Synchronization Gap

With the emergence of autonomous AI coding agents pair-programming on production repositories, code modifications happen rapidly across multiple abstraction layers. Traditional linters (e.g. Flake8, Ruff, Pylint) verify syntax and structural style, while type checkers (Mypy, Pyright) enforce static type contracts.

However, **documentation staleness remains fundamentally unmonitored**:
1. When an agent changes an internal threshold, an exception contract, or a parameter default, documentation frequently goes stale silently.
2. Conversely, naive diffing tools or LLM-based docstring checkers cause **alert fatigue and invalid doc churn**, encouraging agents to blindly rewrite docstrings on pure internal refactorings.

PyDocSync solves this with **deterministic, multi-representation AST fingerprinting, an extensible change impact classifier, and structured AI governance with mandatory audit reasons**.

---

## 2. Theoretical Architecture

```text
                                Python Source Code
                                        │
                                        ▼
                           Canonical AST Extraction
                      (Strip locations & leading docstrings;
                           preserve semantic ctx & names)
                                        │
                                        ▼
                  Multi-Representation Fingerprint Generator
   ┌───────────┬───────────┬────────────┬───────────┬─────────────┬──────────────┬─────────────┐
   ▼           ▼           ▼            ▼           ▼             ▼              ▼             ▼
  CODE        API         TYPE         DOC     RAISE_TYPE   RAISE_DETAIL      EXAMPLE       TOTAL
(Body AST) (Params/Kinds)(Annotations)(Docstring)(Exc Types)  (Exc Constraints)(Doctests)   (SHA-256)
                                        │
                                        ▼
                           AST Change Impact Classifier
                                 (Rules Engine)
                                        │
                 ┌──────────────────────┼──────────────────────┐
                 ▼                      ▼                      ▼
        CANDIDATE_LOW_IMPACT       HIGH_IMPACT              UNKNOWN
      (review_required = False) (review_required = True) (review_required = True)
                 │                      │                      │
                 ▼                      └───────────┬──────────┘
             PASS / CI                              ▼
                                             PYPYDOCSYNC001 Failure
                                          (Emits exact AST delta)
                                                    │
                                     ┌──────────────┴──────────────┐
                                     ▼                             ▼
                           Update Documentation           Explicit Acknowledgment
                            (Sync docstring)          (CLI: pypydocsync accept --reason)
```

---

## 3. Scientific Evolution & Falsification History

PyDocSync was developed through rigorous Spec-Driven Development (SDD) across three consecutive milestones:

### Milestone 1: Core Engine (`001-pydocsync-core`)
- Implemented the 7 representation fingerprints and baseline engine.
- Synthetic PoC across 15 initial test fixtures achieved 100% pass rate.

### Milestone 2: Adversarial Stress Testing (`002-pydocsync-adversarial-stress`)
- To avoid confirmation bias, we attacked frozen Classifier v0.1 using an automated **dual-execution runtime evidence harness** across 16 adversarial scenarios.
- **Discovered Blind Spots in v0.1**: Evaluation order shifts (`ADV01`, `ADV06`) and dictionary key insertion reordering (`ADV10`).
- **Evolved to Classifier v0.2**: Implemented `CallSequenceOrderRule` and `DictKeyOrderRule`, resolving call sequence and dict order escapes.
- **Fundamental AST Boundary Discovery**: Formally cataloged heap aliasing (`a = b` vs `a = list(b)`) as a documented AST boundary limitation.

### Milestone 3: Real-Project Empirical Evaluation (`003-pydocsync-real-evaluation`)
- Evaluated frozen PyDocSync v0.2 against **67 real production symbols** across 15 realistic AI-style development modifications.
- Evaluated against independent **blind human review consensus** (Reviewer A & B).
- **Separated Review Requirement from Update Requirement**:
  - In cases where review was required but existing docs remained accurate, AI agents cleanly used `pypydocsync accept` with **0.0% unnecessary documentation churn**.

---

## 4. Empirical Benchmark Results (v0.2)

| Metric | Observed Benchmark Value | Meaning |
|---|:---:|---|
| **Observed Empirical Recall** | **100.0%** (11 / 11) | Zero observed escapes on human-labeled review-required cases. |
| **Observed Empirical Precision** | **78.6%** (11 / 14) | High signal-to-noise ratio on realistic codebase modifications. |
| **Conservative Over-Trigger Rate** | **20.0%** (3 / 15) | 3 safe internal refactors prompted review due to added string constants. |
| **Unnecessary Doc Churn Rate** | **0.0%** (0 / 15) | Zero invalid/pointless docstring rewrites by AI agents. |
| **Inter-Reviewer Agreement** | **100.0%** (15 / 15) | Complete agreement between independent blind human reviewers. |
| **Full Production Scan Time** | **49.97 ms** | Extremely fast sub-50ms scan across 6 modules and 67 symbols. |
| **Automated Test Suite** | **54 / 54 Passed (100%)** | Zero regressions across Core, Adversarial, and Real evaluation suites. |

---

## 5. Next Steps on the Public Roadmap

1. **Multi-Repository Validation**:
   - Run frozen PyDocSync against 2–3 independent external open-source Python repositories (e.g. `fastapi`, `click`, or `requests` components).
2. **Phase 2 Call-Graph Integration (Spashta CKG)**:
   - Propagate callee signature/exception changes up the call graph to detect transitive caller docstring obligations.
3. **Public GitHub Release & RFC Publication**:
   - Package standalone `packages/pypydocsync` as an open-source PyPI tool and reference architecture for AI-assisted software governance.
