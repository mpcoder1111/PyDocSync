# PyDocSync — Agent Context & Rules

**PyDocSync**: Deterministic Code–Documentation Synchronization for AI-Assisted Python Codebases.

For additional context about this project's technologies, architecture decisions, coding standards,
and development workflow, read the following files in order:

1. `.specify/memory/constitution.md` — project principles and governance (MUST read first)
2. `.specify/memory/standards/coding_standards.json` — Python coding rules (use `_task_index`)
3. `.specify/memory/standards/readme_standards_plan.json` — how to write specs and plans
4. `.specify/memory/standards/readme_standards_shipped.json` — how to write Module READMEs

If a Feature Specification exists for the current work, read it:
`specs/[###-feature-name]/spec.md` and `plan.md`

---

## Spec-Driven Development (SDD) Workflow & Skills

Features follow the strict SDD lifecycle: `specify` → `clarify` → `plan` → `tasks` → `implement` → `converge`.
Shipped specs are immutable historical records; new iterations require a newly numbered spec.

| SDD Phase | Command / Skill | Primary Path | Description |
|---|---|---|---|
| **1. Specify** | `/speckit-specify` | `.agents/skills/speckit-specify/SKILL.md` | Draft intent-first, user-story-driven `spec.md` |
| **2. Clarify** | `/speckit-clarify` | `.agents/skills/speckit-clarify/SKILL.md` | Resolve ambiguities via structured decision tables |
| **3. Plan** | `/speckit-plan` | `.agents/skills/speckit-plan/SKILL.md` | Technical design, grounded research, architecture contracts |
| **4. Tasks** | `/speckit-tasks` | `.agents/skills/speckit-tasks/SKILL.md` | Dependency-ordered `tasks.md` aligned to user stories |
| **Convert Tasks** | `/speckit-taskstoissues` | `.agents/skills/speckit-taskstoissues/SKILL.md` | Convert tasks into trackable GitHub issues |
| **5. Implement**| `/speckit-implement` | `.agents/skills/speckit-implement/SKILL.md` | Test-driven implementation through scoped gate |
| **Converge** | `/speckit-converge` | `.agents/skills/speckit-converge/SKILL.md` | Verify code against spec/contracts and sync artifacts |
| **Checklist** | `/speckit-checklist` | `.agents/skills/speckit-checklist/SKILL.md` | Quality gates and verification check before shipping |
| **Analyze** | `/speckit-analyze` | `.agents/skills/speckit-analyze/SKILL.md` | Cross-artifact consistency and risk analysis |

---

## Pre-Execution Contracts & Idea Maturation

- **Idea Maturation Pipeline (`ideas/`)**:
  - `ideas/arch_*.md` — Architecture Notes for cross-cutting design decisions (written before specs).
  - `ideas/future_features.md` — Deferred feature backlog; items here are NOT being implemented yet.
  - When a new idea is raised but not actioned → add to `ideas/future_features.md`. When a deferred item moves to active dev → run `/speckit-specify <name>` and remove it from backlog.
- **Specification Trigger**: Once an `ideas/` note is ratified, it triggers the formal SDD lifecycle via `/speckit-specify`.
- **Pure Python Domain Contracts**: Core AST parsers, fingerprint extractors, and classifier rules live as clean, typed Python contracts with zero runtime dependencies.

---

## Implemented Ledger (PyDocSync Milestones)

<!--
  MAINTENANCE RULE (keep this file scannable across agent sessions):
  - One Implemented: ###-feature entry per shipped feature, newest first.
  - Keep only the newest ~7 features in full inline here.
  - Never delete an entry — archive it when new features ship.
-->

- **Implemented**: `007-pydocsync-release-audit` (2026-08-29)
  - **Summary**: Pre-release security, schema versioning, AST determinism, and policy audit for `pydocsync-0.2.0`. Added explicit `schema_version: 1` envelope to baseline lockfiles with legacy fallback, enforced strict input validation on `pydocsync accept` (rejecting whitespace/empty reasons and non-existent symbols with standard exit codes), unit tested AST normalization invariants (`ctx` Load/Store/Del preservation and location stripping), verified path traversal isolation and disk freshness across 90 automated tests passing 100% in 2.35s.
  - **Spec & Plan**: [`specs/007-pydocsync-release-audit/spec.md`](specs/007-pydocsync-release-audit/spec.md) | [`plan.md`](specs/007-pydocsync-release-audit/plan.md) | [`release_audit_report.md`](specs/007-pydocsync-release-audit/release_audit_report.md) | [`convergence_report.md`](specs/007-pydocsync-release-audit/convergence_report.md)
  - **Tests**: `tests/` (90/90 passed).

- **Implemented**: `006-pydocsync-consumer-integration` (2026-08-29)
  - **Summary**: External consumer workflow verification on isolated repositories using only the installed `pydocsync-0.2.0` wheel distribution. Verified full AI-agent pair programming lifecycle (`pydocsync init` -> `pydocsync check` -> simulated code drift -> `PYDOCSYNC001` exit 1 -> `pydocsync accept` with audit reason -> `pydocsync check` exit 0), argument validation (exit 2), programmatic Python API (`from pydocsync import check, init, accept, SyncResult`), and zero source coupling.
  - **Spec & Plan**: [`specs/006-pydocsync-consumer-integration/spec.md`](specs/006-pydocsync-consumer-integration/spec.md) | [`plan.md`](specs/006-pydocsync-consumer-integration/plan.md) | [`consumer_integration_report.md`](specs/006-pydocsync-consumer-integration/consumer_integration_report.md) | [`convergence_report.md`](specs/006-pydocsync-consumer-integration/convergence_report.md)
  - **Tests**: `tests/consumer_integration/` (passed).

- **Implemented**: `005-pydocsync-library-hardening` (2026-08-29)
  - **Summary**: Hardened PyDocSync into an experimental standalone Python library (`0.2.0`). Encapsulated internal AST, fingerprint, and classifier machinery behind a minimal top-level public API (`from pydocsync import check, init, accept, SyncResult`), configured PEP 517 packaging in `pyproject.toml` with console script entrypoint, added PEP 561 `py.typed` marker, created `__main__.py`, authored developer documentation, and verified zero external dependencies.
  - **Spec & Plan**: [`specs/005-pydocsync-library-hardening/spec.md`](specs/005-pydocsync-library-hardening/spec.md) | [`plan.md`](specs/005-pydocsync-library-hardening/plan.md) | [`hardening_report.md`](specs/005-pydocsync-library-hardening/hardening_report.md) | [`convergence_report.md`](specs/005-pydocsync-library-hardening/convergence_report.md)
  - **Tests**: `tests/test_public_api.py` (passed).

- **Implemented**: `004-pydocsync-external-corpus-evaluation` (2026-08-29)
  - **Summary**: Multi-repository empirical generalization benchmark across 3 distinct Apache-2.0 pure-Python open-source codebases (Dulwich, Janome, python-sdb) covering 61 external symbols and 20 realistic AI modifications. Evaluated against independent dual blind human review consensus (Reviewer A & B), achieving 100.0% observed recall (13/13), 100.0% precision (13/13), 0.0% churn, and a 15.0% UNKNOWN escalation rate.
  - **Spec & Plan**: [`specs/004-pydocsync-external-corpus-evaluation/spec.md`](specs/004-pydocsync-external-corpus-evaluation/spec.md) | [`plan.md`](specs/004-pydocsync-external-corpus-evaluation/plan.md) | [`external_evaluation_report.md`](specs/004-pydocsync-external-corpus-evaluation/external_evaluation_report.md) | [`convergence_report.md`](specs/004-pydocsync-external-corpus-evaluation/convergence_report.md)
  - **Tests**: `tests/external_evaluation/` (passed).

- **Implemented**: `003-pydocsync-real-evaluation` (2026-08-29)
  - **Summary**: Real-project empirical evaluation across 67 production symbols in `pydocsync/` evaluated against 15 realistic AI development modifications with independent blind human review consensus (Reviewer A & B). PyDocSync v0.2 achieved 100.0% observed recall, 78.6% precision, 0.0% unnecessary documentation churn, and 49.97 ms full-package scan time.
  - **Spec & Plan**: [`specs/003-pydocsync-real-evaluation/spec.md`](specs/003-pydocsync-real-evaluation/spec.md) | [`plan.md`](specs/003-pydocsync-real-evaluation/plan.md) | [`real_evaluation_report.md`](specs/003-pydocsync-real-evaluation/real_evaluation_report.md) | [`convergence_report.md`](specs/003-pydocsync-real-evaluation/convergence_report.md)
  - **Tests**: `tests/real_evaluation/` (passed).

- **Implemented**: `002-pydocsync-adversarial-stress` (2026-08-29)
  - **Summary**: Automated dual-execution behavioral falsification harness under `tests/adversarial/` (16 attack cases). Evaluated frozen Classifier v0.1 against empirical runtime execution evidence, discovering 4 potential blind spots and 3 potential over-triggers. Evolved to Classifier v0.2 with `CallSequenceOrderRule` and `DictKeyOrderRule`, resolving call order and dict insertion blind spots with zero core regressions. Documented heap aliasing as a fundamental AST boundary.
  - **Spec & Plan**: [`specs/002-pydocsync-adversarial-stress/spec.md`](specs/002-pydocsync-adversarial-stress/spec.md) | [`plan.md`](specs/002-pydocsync-adversarial-stress/plan.md) | [`adversarial_evaluation_report.md`](specs/002-pydocsync-adversarial-stress/adversarial_evaluation_report.md) | [`convergence_report.md`](specs/002-pydocsync-adversarial-stress/convergence_report.md)
  - **Tests**: `tests/adversarial/` (passed).

- **Implemented**: `001-pydocsync-core` (2026-08-29)
  - **Summary**: Standalone representation synchronization framework in `pydocsync/`. Multi-representation AST fingerprinting (`CODE`, `API`, `TYPE`, `DOC`, `RAISE_TYPE`, `RAISE_DETAIL`, `EXAMPLE`), extensible change impact classifier (High / Low / Unknown), modular JSON baselines, and `pydocsync accept` CLI acknowledgment with machine-readable `PYDOCSYNC001` feedback for AI coding agents.
  - **Spec & Plan**: [`specs/001-pydocsync-core/spec.md`](specs/001-pydocsync-core/spec.md) | [`plan.md`](specs/001-pydocsync-core/plan.md) | [`convergence_report.md`](specs/001-pydocsync-core/convergence_report.md)
  - **Tests**: `tests/test_fingerprint.py`, `tests/test_classifier.py`, `tests/test_integration.py` (passed).

---

## Agent Quick Navigation

**Read `constitution.md` once per session.** Then use this table — look up only what you need.

| I am about to… | Read first |
|---|---|
| Run tests after an edit | **Testing discipline** below — run the SCOPED gate |
| Write a Python tool, service, or model | `coding_standards.json` → `_task_index` for your task type |
| Write or update a spec, plan, or arch note | `readme_standards_plan.json` |
| Write a module README | `readme_standards_shipped.json` |
| Change or add a core data model | Sketch typed dataclasses / schema contracts |
| Record a durable fact / lesson / decision | Add conformant `knowledge/` atom, not prose bloat in `AGENTS.md` |

---

## Testing Discipline (Scoped Gate)

- Run tests strictly using the local virtual environment:
  ```powershell
  .\.venv\Scripts\pytest.exe tests/
  ```
- **Scoped Gate**: Run only tests for the specific module or rule touched (`pytest tests/test_<module>.py`).
- **Full Suite**: Run full suite before completing any SDD feature or release.

---

## Governance Tier for Changes (see Constitution)

| Tier | Example | Required |
|---|---|---|
| **T1 trivial** | Docstring fix, type annotation, 1-line tweak | Direct — no ceremony |
| **T2 bounded** | New utility function, standalone helper, test addition | Scoped unit tests + standard audit |
| **T3 behavioral** | New classifier rule, API endpoint change, CLI alteration | Full SDD spec-kit + impact check |
| **T4 structural** | Architecture overhaul, baseline schema migration | Spec + Architecture DR + Constitution check |

---

## Documentation & Code Style Standards

1. **Module Docstrings**:
   - Every `.py` file starts with a comprehensive header docstring: `WHAT IS THIS?`, `WHY DO WE NEED THIS?`.
2. **Function & Class Docstrings (Google Style)**:
   - Strict Google Style (`Args:`, `Returns:`, `Raises:`, `Example:`).
3. **Type Annotations**:
   - 100% type coverage on all public functions/classes using modern Python 3.10+ syntax (`str | None`, `list[dict[str, Any]]`).
   - `py.typed` marker file included.
4. **Clean Inline Comments**:
   - Comments explain *why* (non-obvious decisions, edge cases, domain rules), never restating *what* the code visibly does.
