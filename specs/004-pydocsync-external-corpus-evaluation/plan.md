# Implementation Plan: 004-pypydocsync-external-corpus-evaluation

**Branch**: `004-pypydocsync-external-corpus-evaluation` | **Date**: 2026-08-29 | **Spec**: [`specs/004-pypydocsync-external-corpus-evaluation/spec.md`](spec.md)  
**Input**: Feature specification from `specs/004-pypydocsync-external-corpus-evaluation/spec.md`  

---

## Summary

Conduct a multi-repository generalization evaluation of frozen PyDocSync v0.2 across 3 diverse, permissively licensed (Apache-2.0) pure-Python open-source codebases (Dulwich, Janome, python-sdb / bitcode). Ingest 60+ external symbols into a read-only corpus, execute 20+ realistic AI development scenarios against frozen v0.2 without per-project customizations, compare predictions against blind human review consensus, and measure cross-codebase precision, recall, and churn.

---

## Technical Context

- **Corpora Archetypes (Apache-2.0 Pure-Python)**:
  1. **Dulwich** (Git internals & network protocol): Pinned commit `jelmer/dulwich@v0.21.7`.
  2. **Janome** (Japanese morphological tokenizer & dictionary): Pinned commit `mocobeta/janome@v0.5.0`.
  3. **python-sdb / bitcode** (Binary struct/serialization engine): Pinned commit `williballenthin/python-sdb@v0.1.0`.
- **Infrastructure**: Dedicated test suite in `packages/pypypydocsync/tests/external_evaluation/` with `corpus_manifest.json`.
- **Methodology**: Pinned read-only ingestion → frozen v0.2 classification → dual blind human consensus → tri-part metrics.
- **Reporting**: Automated report generator outputting to `specs/004-pypydocsync-external-corpus-evaluation/external_evaluation_report.md`.

---

## Constitution Check

*Constitution: `.specify/memory/constitution.md` | Standards: `.specify/memory/standards/`*

| Gate | Principle | Status | Notes |
|---|---|---|---|
| Does this feature keep business logic pure Python with zero framework coupling? | I. Two-Layer Architecture | **YES** | Standalone benchmark runners and pure standard library execution. |
| Is a `spec.md` present and complete before this plan was written? | II. Spec-Driven Development | **YES** | `specs/004-pypydocsync-external-corpus-evaluation/spec.md` created. |
| Is the third-party corpus read-only with clean licensing? | VII. Graph & State Safety | **YES** | Apache-2.0 sources referenced with pinned commits; upstream untouched. |
| Is Classifier v0.2 strictly frozen across all external projects? | V. Deterministic Platform | **YES** | Zero per-project rule tuning permitted. |

---

## Project Structure & File Layout

```text
packages/pypypydocsync/tests/external_evaluation/
├── __init__.py
├── corpus_manifest.json               # Pinned repository metadata, commits & licenses
├── corpus/                            # Representative modules from external projects
│   ├── dulwich_pack.py                # Dulwich Git packfile parsing sample
│   ├── janome_tokenizer.py           # Janome morphological tokenization sample
│   └── sdb_struct.py                  # python-sdb binary structure unpacking sample
├── scenarios.py                       # 20+ realistic AI-style code modification diffs
├── human_assessments.py               # Blind human review dataset (Reviewer A & B)
└── test_external_evaluation.py        # Automated multi-repo test runner & report generator

specs/004-pypydocsync-external-corpus-evaluation/
├── spec.md                            # Specification
├── plan.md                            # This file
├── tasks.md                           # Dependency-ordered tasks
└── external_evaluation_report.md      # Final cross-repository empirical report
```

---

## Execution Workflow & Roadmap

1. **Phase 1 (Corpus Ingestion & Baselining)**:
   - Create `corpus_manifest.json` referencing Dulwich, Janome, and python-sdb.
   - Establish baseline lockfiles for 60+ external symbols across the 3 representative modules.
2. **Phase 2 (Cross-Repository AI Modification Scenarios & Blind Review)**:
   - Author 20+ realistic development modifications across all 3 external projects in `scenarios.py`.
   - Record independent blind human assessments (Reviewer A & B) in `human_assessments.py`.
3. **Phase 3 (Automated Multi-Repo Evaluation & Profiling)**:
   - Implement `test_external_evaluation.py` to evaluate frozen PyDocSync v0.2 across all 20+ external scenarios.
   - Profile scanning speed and verify zero regressions on the 54 existing tests.
4. **Phase 4 (Final Generalization Report & Convergence)**:
   - Export `external_evaluation_report.md`.
   - Run `/speckit-converge`.
