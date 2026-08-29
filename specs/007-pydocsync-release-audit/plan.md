# Implementation Plan: 007-pypydocsync-release-audit

**Branch**: `007-pypydocsync-release-audit` | **Date**: 2026-08-29 | **Spec**: [`specs/007-pypydocsync-release-audit/spec.md`](spec.md)  
**Input**: Release audit requirements and checklist  

---

## Summary

Perform a pre-release security, schema versioning, AST determinism, and documentation audit on PyDocSync 0.2.0. Enhance lockfile envelopes with `schema_version: 1`, enforce strict validation on `pypypydocsync accept` (rejecting blank reasons and non-existent symbols), test AST normalization invariants (preserving `ctx` and constants while stripping line locations), and revise `packages/pypypydocsync/README.md` to document the 3 drift layers, symbol monitoring policies, trust model, and benchmark-scoped metrics.

---

## Technical Context

- **Baseline Lockfile Envelope Format**:
  ```json
  {
    "schema_version": 1,
    "pypydocsync_version": "0.2.0",
    "fingerprint_algorithm": "sha256",
    "symbols": {
      "symbol_qualname": {
        "code": "...",
        "api": "...",
        "types": "...",
        "doc": "...",
        "raise_type": "...",
        "raise_detail": "...",
        "example": "...",
        "last_reviewed_at": "...",
        "audit_reason": "..."
      }
    }
  }
  ```
- **Accept Validation Invariants**:
  - `reason.strip()` must be non-empty.
  - Symbol must exist in the target module.
  - Fingerprints are generated against current physical disk content.
- **AST Normalization Tests**:
  - Location stripping (`lineno`, `col_offset`, `end_lineno`, `end_col_offset`).
  - Context preservation (`ast.Load`, `ast.Store`, `ast.Del`).
  - Python 3.10, 3.11, 3.12, 3.13 standard AST compliance.

---

## Execution Workflow & Roadmap

1. **Phase 1 (Baseline Schema Versioning & Lockfile Upgrade)**:
   - Update `packages/pypypydocsync/pypydocsync/baseline.py` to write and read `schema_version: 1` envelopes (with backward-compatibility for legacy lockfiles).
   - Re-initialize production baselines under `.project/pypypydocsync/`.
2. **Phase 2 (Accept Validation & Security Hardening)**:
   - Update `packages/pypypydocsync/pypydocsync/cli.py` to strictly reject empty/whitespace reasons and non-existent symbols.
3. **Phase 3 (AST Normalization Invariants Test Suite)**:
   - Author `packages/pypypydocsync/tests/test_ast_invariants.py` verifying location stripping and `ctx` semantic preservation.
4. **Phase 4 (Documentation & Trust Model Polish)**:
   - Update `packages/pypypydocsync/README.md` with:
     - The 3 Drift Layers (A. Missing info, B. Contract drift, C. Implementation drift).
     - Symbol Selection Policy (public top-level callables & classes).
     - Trust & Authorization Model (`accept` as human/agent review record).
     - Public API Stability Statement.
     - Scoped empirical benchmark wording.
5. **Phase 5 (Full Test Suite Regression & Release Candidate Build)**:
   - Verify all 85+ tests passing 100%.
   - Build clean `.whl` and generate `specs/007-pypydocsync-release-audit/release_audit_report.md`.
