# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Constitution: `.specify/memory/constitution.md` | Standards: `.specify/memory/standards/`*

**Step 1 — Read relevant standards files before filling this section:**

| What you are doing in this plan | Standards file to read first |
|---|---|
| Writing any Python module or Django app | `.specify/memory/standards/coding_standards.json` → `_task_index` |
| Writing any CSS, template, or JS | `.specify/memory/standards/frontend_rules.json` → `_task_index` |
| Writing this plan doc | `.specify/memory/standards/readme_standards_plan.json` → `_usage` |
| Writing a shipped README for this feature | `.specify/memory/standards/readme_standards_shipped.json` → `_usage` |

**Step 2 — Answer each gate. Any `NO` or `UNCLEAR` must be resolved before proceeding.**

| Gate | Principle | Answer |
|------|-----------|--------|
| Does this feature keep business logic in `forms_toolkit/` (Layer 1)? | I. Two-Layer Architecture | YES / NO / N/A |
| Is a `spec.md` present and complete before this plan was written? | II. Spec-Driven Development | YES / NO |
| Are Layer 1 tests written before implementation (TDD)? | III. Bottom-Up Test-First | YES / NO / N/A |
| Does the frontend use HTMX + Django templates only (no React/Vue/Angular)? | IV. HTMX-First Frontend | YES / NO / N/A |
| Have new Python files been checked against `coding_standards.json`? | V. Python Code Quality | YES / NO / N/A |
| Has `frontend_components.json` been checked before creating any frontend asset? | VI. Frontend Component Catalog | YES / NO / N/A |
| Are new docs assigned the correct type (Plan or Shipped) per readme_standards files? | VII. Documentation Lifecycle | YES / NO / N/A |
| If this feature touches forms/responses/schema: does it respect draft/published split, FormVersion immutability, soft-delete, and UUID stability? | VIII. Schema Versioning & Immutability | YES / NO / N/A |
| If this feature triggers auditable events (publish, archive, delete, collaborator change, ownership transfer; group create/soft-delete/clone/visibility/clonable/member/access changes; or user permission grant/revoke): does services.py write to portal_core_auditlog? | IX. Auditability | YES / NO / N/A |

**Step 3 — Fill in the contracts/ folder plan for this feature:**

`contracts/` in `.specify/specs/[###-feature-name]/contracts/` holds **this feature's** interface
specs only. Examples:
- `api-spec.json` — REST endpoints exposed or consumed by this feature
- `data-model.md` — DB schema / Django models for this feature
- `htmx-partials.md` — HTMX endpoints and their response shapes

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete rows that are not needed. The delivered plan must
  not include placeholder comments — only actual paths.

  Forms Portal uses a two-layer structure:
    Layer 1: forms_toolkit/<module>/    — pure Python, no Django, no DB
    Layer 2: <app_name>/               — Django app (views, services, models, templates)

  Layer 1 is mandatory for all business logic. Layer 2 is mandatory for HTTP/DB/UI.
-->

```text
# Layer 1 — forms_toolkit (if this feature adds business logic)
forms_toolkit/
└── [new_module]/
    ├── __init__.py
    ├── [module].py           # business logic
    └── README_[module].md    # shipped README (after feature complete)

tests/forms_toolkit/
└── test_[module].py          # pure pytest, no Django

# Layer 2 — Django app (edit/create as needed for this feature)
[app_name]/
├── models.py                 # or models/ package if complex
├── services.py               # glue between forms_toolkit/ and DB
├── views.py
├── urls.py
├── admin.py                  # only if admin pages needed
├── templates/[app_name]/
│   ├── partials/             # HTMX response partials
│   └── [page].html
└── tests/
    ├── test_models.py        # pytest-django
    ├── test_services.py      # pytest-django
    └── test_views.py         # Django test client

# DB schema (REQUIRED if any model changes)
db/schema.dbml                # update in SAME commit as model changes
docs/architecture/schema.svg  # regenerate: python scripts/generate_schema_diagram.py
docs/architecture/schema.png  # commit both diagram files in the SAME commit as DBML
```

**Structure Decision**: [State which apps and modules are affected, and whether new apps or modules are added]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
