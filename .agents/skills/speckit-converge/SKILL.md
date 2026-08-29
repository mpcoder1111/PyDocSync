---
name: "speckit-converge"
description: "Verify implementation against specification contracts and synchronize artifacts before shipping."
argument-hint: "Optional focus areas or component names"
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/converge.md"
user-invocable: true
disable-model-invocation: false
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before convergence)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_converge` key.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each executable hook, prompt or execute per standard hook behavior.

## Goal

The **Convergence Loop (`/speckit-converge`)** verifies that the actual code implementation matches the commitments in `spec.md`, `plan.md`, `contracts/`, and `tasks.md`. It identifies:
1. **Unimplemented commitments** (requirements or scenarios in `spec.md` with missing code/tests).
2. **Implementation drift** (actual tool names, arguments, return schemas, or error types that evolved during coding and differ from the spec/contract).
3. **Undocumented behavior** (new parameters or capabilities added in code but omitted from documentation).
4. **Contract conformance** (verifying Layer-1 / Layer-2 boundaries, typed signatures, and test coverage).

## Operating Rules

1. **Grounded Code Inspection**: Inspect actual codebase files, tests, and signatures—do NOT guess.
2. **Bi-Directional Alignment**:
   - If the code intentionally evolved to handle a better design or edge case, provide recommendations to update `spec.md` and `plan.md` to reflect the shipped reality.
   - If the code missed a required user story or acceptance scenario, flag it as an **Implementation Gap**.
3. **Constitution Check**: Validate all changes against `.specify/memory/constitution.md`.

## Execution Steps

### 1. Initialize Context
- Load current feature directory from `.specify/feature.json` or active branch.
- Identify the core artifacts: `spec.md`, `plan.md`, `tasks.md`, and any `contracts/`.

### 2. Compare Specification vs Code
- **User Stories & Acceptance Scenarios**: Check that each user scenario in `spec.md` has corresponding implementation and unit tests.
- **Contract & Signature Check**: Compare tool signatures, inputs, and outputs against `contracts/` and `plan.md`.
- **Tasks Verification**: Verify that all tasks marked as completed `[x]` in `tasks.md` exist and are tested.

### 3. Run Quality & Test Validation
- Run scoped tests for the feature.
- Verify docstring completeness (Google style) and type annotations.
- Verify Layer 1 vs Layer 2 architectural boundaries.

### 4. Output Convergence Report

Output a structured report formatted as:

```markdown
# Convergence Report: [FEATURE NAME]

## 1. Executive Summary
- **Status**: [CONVERGED / DRIFT DETECTED / GAPS FOUND]
- **Summary**: Brief assessment of alignment between spec and implementation.

## 2. Parity Assessment
| Requirement / Story | Spec Commitment | Implemented In | Status |
|---|---|---|---|
| US1: [Name] | [Expected behavior] | `path/to/file.py` | MATCH / DRIFT / MISSING |

## 3. Contract & Signature Drift
- [List any signature or schema discrepancies between contracts/plan and actual code]

## 4. Quality & Governance Gates
- [x] Scoped unit tests passing
- [x] Layer boundary check passed
- [x] Type annotations complete
- [x] Docstrings complete

## 5. Recommended Actions
- [Specific updates needed to sync spec.md / plan.md / code before shipping]
```

### 5. Check for Extension Hooks
- Check `.specify/extensions.yml` for `hooks.after_converge` entries and execute/prompt accordingly.
