# Feature Specification: 009-silent-false-pass-hardening

## Eliminate Silent "All Synchronized" Results (Corrupt Baselines, Unparseable Files, Ambiguous Accept, Unguarded Init)

**Feature Code**: `009-silent-false-pass-hardening`  
**Created**: 2026-09-19  
**Status**: Implemented (Q1-Q11 resolved; awaiting owner review and convergence sign-off)  
**Input**: External user field report against v0.3.0 — items 1–4 of the "Must fix" table. Root causes confirmed by reading the code (see Evidence).

> **Agent note:** Plan-stage document. Follow `.specify/memory/standards/readme_standards_plan.json`.
> Governance tier: **T3 behavioral** (CLI behavior and exit-code contract change) — full SDD required.

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Principle IV (Fail-Safe) is the driver |
| 2 | [Evidence From Current Code](#evidence-from-current-code) | Root cause of each reported gap |
| 3 | [User Scenarios & Testing](#user-scenarios--testing) | US1 corrupt baseline, US2 unparseable files, US3 ambiguous accept, US4 init overwrite, US5 same-file duplicate names, US6 stale baseline after a documented change |
| 4 | [Requirements](#requirements) | FR-001 … FR-020 |
| 5 | [Success Criteria](#success-criteria) | Measurable outcomes |
| 6 | [Assumptions & Boundaries](#assumptions--boundaries) | In/out of scope; deferred items 5–11 |
| 7 | [Clarifications](#clarifications) | Q1–Q6 resolved; regression test matrix |

---

## Applicable Constitution Principles

| Principle | Applies? | Notes |
|---|---|---|
| **I. Pure Standard Library Architecture** | **YES** | No new dependencies. |
| **II. Spec-Driven Development (SDD)** | **YES** | This spec. Spec 008 is shipped and immutable; this is a new numbered iteration. |
| **III. Deterministic Representation Synchronization** | **YES** | Diagnostics and ordering must be deterministic (sorted, stable output). |
| **IV. Gated Safety & Explicit Review Acknowledgment** | **YES — primary** | "Route ambiguous cases to review rather than silently assuming safe." All four gaps are silent-safe assumptions. |
| **V. Automated Verification & Scoped Testing** | **YES** | Each gap requires a regression test that fails on v0.3.0. |

---

## Evidence From Current Code

| # | Reported gap | Root cause (v0.3.0) |
|---|---|---|
| 1 | Corrupt baseline → exit 0 | `BaselineManager.load_module_baseline` returns `{}` on `JSONDecodeError`/`OSError`, so unreadable is indistinguishable from "no baseline"; every symbol is then treated as *new*, and new documented symbols pass. It also returns `{}` for a JSON value that is not an object, and a record with missing/extra keys raises an unhandled `TypeError` in `BaselineRecord.from_dict`. |
| 2 | Unparseable file skipped | `scan_and_check`, `accept_symbol_review` and `initialize_baseline` each wrap read + `extract_symbols_from_source` in `except Exception: continue`. |
| 3 | `accept` binds to first file | `accept_symbol_review` iterates sorted files and returns on the first `sym.qualname == symbol_qualname`. Qualnames are class-scoped only (e.g. `Command.handle`), not module-qualified, and baselines are stored per file, so identical names collide. No file selector exists in the CLI or API. |
| 4 | `init` overwrites drift | `initialize_baseline` calls `record_symbol_baseline` for every symbol unconditionally; existing records (including drifted ones) are replaced with no check or warning. |
| 6 | Files with a docstring-only class silently skipped (found during implementation, verified on the v0.3.0 source) | The extractor strips the docstring, leaving an empty class body that `ast.unparse`/`ast.parse` cannot round-trip; the resulting `SyntaxError` was swallowed by `except Exception: continue`, so the **whole file** was skipped: `init` baselined 0 symbols and drift in the same file was never reported. Very common shape (exception classes). With US2 fixed this would have turned valid projects red, so it is fixed here (FR-021). |
| 5 | Sticky doc baseline (found in planning, reproduced by the reporter) | `check` suppresses a failure whenever the stored doc fingerprint differs from the current one, and nothing ever refreshes the stored record after a legitimate code+doc update. From then on the doc fingerprint always differs, so every later code-only change is suppressed. |

Cross-cutting: `main()` maps any `ValueError` to exit 2 (item 10). Now in scope: new failure conditions MUST NOT depend on that broad catch (FR-012).

---

## User Scenarios & Testing

### User Story 1 — Corrupt or Unreadable Baseline Fails Loudly (Priority: P1)

As a CI owner, I want `check` to refuse to report success when any baseline file cannot be read or has an invalid structure, so that a damaged or truncated lockfile can never silently disable drift detection.

**Why this priority**: Silent wrong "all fine" result; defeats the tool's core purpose.

**Independent Test**: Write `{ not json` into an existing module baseline, run `check`.

**Acceptance Scenarios**:
1. **Given** a valid baseline where one module's lockfile contains invalid JSON, **When** `check` runs, **Then** it does NOT print "All symbols synchronized", exits non-zero, and names the corrupt lockfile and the reason.
2. **Given** a lockfile that is valid JSON but not the expected structure (a list, or a record with missing/unknown fields), **When** `check` runs, **Then** same outcome (no stack trace).
3. **Given** a lockfile that exists but cannot be read (OS/permission error), **Then** same outcome.
4. **Given** a module with **no** lockfile (never baselined), **Then** current behavior is preserved (new-symbol gating only) — absent ≠ corrupt.
5. **Given** several corrupt lockfiles, **Then** all are reported in one run, in sorted order.
6. **Given** a root with no baseline folder at all, **Then** `check` behaves as today by default (an opt-in `--require-baseline` strict mode is deferred to spec 010, Q6).

---

### User Story 2 — Unparseable Source Files Are Reported, Never Skipped (Priority: P1)

As a developer, I want `check` (and `init`) to tell me when a Python file could not be parsed, so a syntax error cannot hide every symbol in that file from review.

**Why this priority**: Silent wrong "all fine" result.

**Independent Test**: A project whose only file has a syntax error; a project with one good and one broken file.

**Acceptance Scenarios**:
1. **Given** a project whose only `.py` file has a syntax error, **When** `check` runs, **Then** it does not report "All symbols synchronized", exits non-zero, and names the file, line and error.
2. **Given** a good file beside a broken one, **When** `check` runs, **Then** the good file is still evaluated (its drift still reported) AND the broken file is reported; the run cannot exit 0.
3. **Given** a file that cannot be read or decoded as UTF-8, **Then** same as scenario 1.
4. **Given** `init` meets an unparseable file, **Then** it reports it and does not present the result as a complete baseline.
5. **Given** a file that is valid on a newer Python but fails on the running interpreter (e.g. `match` statement), **Then** the report states the error kind and line (e.g. `SyntaxError line 12`) so the cause is obvious.
6. **Given** a valid file containing a class whose body is only a docstring (e.g. an exception class), **Then** its symbols are evaluated (never skipped, never reported as unparseable), and drift elsewhere in that file is detected.
7. **Given** a broken file inside an excluded directory (`tests/`, `migrations/`, …), **Then** it is never scanned and never reported.

---

### User Story 3 — `accept` Cannot Silently Acknowledge the Wrong Symbol (Priority: P1)

As an AI agent or reviewer, I want `accept` to act on exactly the symbol I intend, so same-named symbols in different files (`Command.handle`) cannot cause the unchanged one to be baselined while the changed one stays failing.

**Why this priority**: Silent wrong "accepted" result; corrupts the audit trail.

**Independent Test**: Two files each defining `Command.handle`, one drifted; run `accept --symbol Command.handle`.

**Acceptance Scenarios**:
1. **Given** the same qualified name exists in more than one file, **When** `accept` runs without a file selector, **Then** it changes nothing, exits **2** (usage error), lists every candidate file with line number and whether it currently drifts, and prints the exact command to rerun for each candidate with `--file` filled in.
2. **Given** the same situation, **When** the user supplies a file selector matching exactly one candidate, **Then** only that file's baseline is updated, and only that file is read (other files are not scanned).
3. **Given** a symbol in exactly one file, **When** `accept` runs without a selector, **Then** behavior is unchanged (backward compatible).
4. **Given** a symbol that exists in no file, or a selector naming a file that does not contain it, **Then** exit **1** ("not found", unchanged from v0.3.0) and nothing changed.
5. **Given** a selector path that escapes the project root, **Then** it is rejected.
6. **Given** the programmatic `accept(...)` API, **Then** the same disambiguation exists and ambiguity is never resolved silently.
7. **Given** a `PYDOCSYNC001` failure report, **Then** its suggested `accept` command always includes `--file` for that symbol (the tool already knows it), so the hint is correct even for duplicated names.
8. **Given** the same qualified name occurs more than once *inside one file* (property getter + setter, `@overload`), **Then** see US5.
9. **Given** an unparseable file exists and the symbol is found elsewhere, **Then** the unparseable file is reported (it may contain another candidate, so the answer is not definitive).

---

### User Story 4 — `init` Cannot Silently Erase Drift (Priority: P1)

As a developer, I want `init` to never destroy an existing drift signal without an explicit decision, so running it "to make check pass" (forbidden by the consumer skill but not enforced) cannot wipe out a review obligation.

**Why this priority**: Silent erasure of the tool's own signal.

**Independent Test**: Baseline → change a default → `check` fails → run `init` → `check` must still fail (or `init` must refuse).

**Acceptance Scenarios**:
1. **Given** an existing baseline and a symbol that `check` currently flags (same evaluation as `check`), **When** `init` runs without `--force`, **Then** that record is NOT modified, `check` afterwards still fails for it, and `init` prints the number of protected drifted records plus the `accept` and `--force` commands to use next.
2. **Given** any protected record, **Then** `init` exits **1**; with none protected it exits **0**.
3. **Given** an existing baseline plus a **newly added** module/symbol, **When** `init` runs without `--force`, **Then** the new symbols ARE baselined (onboarding still works) while drifted records stay protected.
4. **Given** drift, **When** `init --force` runs **without** `--reason` (or with a blank one), **Then** it changes nothing and exits 2.
5. **Given** drift, **When** `init --force --reason "<why>"` runs, **Then** drifted records are overwritten, each overwritten record stores the reason and is marked acknowledged, and the output states how many were overwritten.
6. **Given** no existing baseline, **Then** behavior is unchanged.
7. **Given** an existing baseline with no drift, **Then** `init` is a harmless no-op for those records.
8. **Given** `init --dry-run`, **Then** it prints what would be baselined and what would be protected (and, with `--force`, overwritten), writes nothing, and exits with the code the real run would produce.
9. **Given** a record that differs from the code but is not flagged by `check` (documentation was updated: a *stale* record, see US6), **When** `init` runs without `--force`, **Then** it is left untouched, reported with the `refresh` command to use, and does not by itself change the exit code.

---

### User Story 5 — Same Qualified Name Inside One File Is Tracked Per Definition (Priority: P1)

*Discovered during clarification; verified on v0.3.0 by the reporter and by us.* When one qualified name is defined more than once in a file, the baseline keeps **one record per name**, so the last definition overwrites earlier ones:
- **Redefinition / `@overload` stubs**: changing the body of the *first* definition gives "All symbols synchronized", exit 0. This is a real silent pass.
- **Property getter + setter**: changing the setter is flagged, but changing the getter is compared against the setter's record, seen as a documentation difference, and suppressed; only the enclosing class is flagged, never `Box.size`. `init` also counts 3 symbols but stores 2.

**Why this priority**: Same silent-pass class as US1–US4.

**Independent Test**: Redefined function, property getter/setter, `@overload`; change each definition in turn.

**Acceptance Scenarios**:
1. **Given** a function defined twice in one file, **When** the body of the *first* definition changes, **Then** `check` reports drift (it does not exit 0).
2. **Given** a property getter and setter, **When** the getter changes, **Then** `check` reports the getter's own symbol (e.g. `Box.size`), not only the enclosing class; changing the setter is reported for the setter.
3. **Given** `@overload` stubs plus an implementation, **When** any one changes, **Then** that definition is reported.
4. **Given** the report for a duplicated name, **When** `accept --symbol X --file f.py` runs, **Then** it acknowledges all definitions of `X` in that file and prints the count (e.g. "3 definitions updated").
5. **Given** an existing v0.3.0 baseline, **When** `check` runs, **Then** it loads without error. For files with duplicated names, v0.3.0 stored only the last definition under the plain key, so a one-time acknowledgment per name (`accept --symbol X --file F`) may be requested; this is documented in the release notes.
6. **Given** existing baseline plus duplicates, **When** `init` runs, **Then** each occurrence is baselined/protected separately, the reported count equals the number of stored records, and drifted occurrences are protected individually.

---

### User Story 6 — A Documented Change Must Not Leave the Symbol Permanently Unguarded (Priority: P1)

*Discovered during planning; independently reproduced by the reporter on v0.3.0.* Baseline `fee()` (docstring "5 percent", code `amount * 0.05`). A developer changes the code to `0.08` and the docstring to "8 percent"; `check` passes — correct, this is the prescribed workflow. Later someone changes only the code to `amount * 0.50`; `check` still says "All symbols synchronized". The baseline holds the *old* docstring fingerprint, so every later code-only change looks like "the doc changed, so it was reviewed". After one legitimate update the symbol is permanently unguarded and `check` never says its baseline is out of date.

**Design constraint**: without a recorded reviewed state, the tool cannot tell step 3 (code-only change) from step 2 (code+doc change): both differ from the old baseline in code and docs. So the fix must (1) make staleness visible, (2) give a non-destructive way to record it, (3) let CI enforce it. `check` alone cannot fail step 3.

**Why this priority**: Happens in the normal, prescribed workflow; same silent-pass class as US1–US4.

**Independent Test**: The three-step `fee()` reproduction.

**Acceptance Scenarios**:
1. **Given** a symbol whose code and docs changed together after baselining, **When** `check` runs, **Then** it passes (exit 0) as before AND reports "N symbol(s) have updated documentation not yet recorded in the baseline", listing file and symbol; `SyncResult.stale` lists them.
2. **Given** the same state, **When** `check --fail-on-stale` runs, **Then** it exits 1 with a distinct message and the `refresh` command to run.
3. **Given** stale symbols, **When** `refresh --reason "<why>"` runs, **Then** exactly those records are re-recorded with the reason; records that `check` flags and symbols with no baseline are never touched; the count is printed.
4. **Given** `refresh` was run after step 2, **When** only the code changes (docstring untouched), **Then** `check` fails with `PYDOCSYNC001` — step 3 of the reproduction.
5. **Given** `refresh` with a missing or blank reason, **Then** it changes nothing and exits 2. `--symbol` / `--file` narrow the refresh.
6. **Given** nothing is stale, **Then** `refresh` is a no-op that exits 0.
7. **Given** a docstring-only edit (code unchanged), **Then** the symbol is also reported stale and is refreshable.
8. **Given** the state without `refresh`, **Then** the stale notice is printed on every `check` (step 2 and step 3 alike) so the gap is visible, and the documentation states the residual limit (FR-020).

---

### Edge Cases

- Empty (0-byte) lockfile → treated as corrupt.
- Lockfile with a `schema_version` newer than supported → reported as unsupported, not read as legacy.
- Legacy (pre-envelope) lockfile that is otherwise valid → still accepted (spec 007 compatibility).
- Corrupt lockfile for a module whose source was deleted (stale baseline) → out of scope (see Boundaries).
- Output order and exit codes are deterministic across runs.

---

## Requirements

- **FR-001**: `check` MUST NOT report success if any baseline lockfile encountered is unreadable, non-JSON, structurally invalid, empty, or of unsupported `schema_version`.
- **FR-002**: Diagnostics for FR-001 MUST name the lockfile path and a human-readable reason, list all offenders (sorted), and be distinguishable from `PYDOCSYNC001` review failures.
- **FR-003**: A missing lockfile MUST remain distinguishable from a corrupt one and keep current "new symbol" semantics.
- **FR-004**: `check` MUST NOT report success if any discovered `.py` file cannot be read, decoded or parsed. Diagnostics MUST include file, line (when available) and error kind.
- **FR-005**: Evaluation MUST continue past a broken file so all drift and all broken files are reported in a single run.
- **FR-006**: `init` MUST report unparseable files and MUST NOT present its result as a complete baseline when any were skipped.
- **FR-007**: `accept` MUST detect when the requested symbol name resolves to more than one file and MUST change nothing in that case, listing all candidates.
- **FR-008**: `accept` MUST provide `--file <path>` (and `file=` in the API), resolved relative to `--root` and constrained to the project root. Ambiguity exits 2 and prints the rerun command per candidate; "not found" keeps exit 1.
- **FR-009**: `accept` on a name resolving to exactly one file MUST behave as in v0.3.0.
- **FR-010**: `init` MUST NOT modify any existing baseline record that `check` currently flags (decided by the same evaluation `check` uses) unless `--force --reason "<text>"` is given; it MUST report the protected count and the next-step `accept` / `--force` commands, and exit 1 when any record was protected. New symbols/modules MUST still be baselined. `--force` without a non-blank reason MUST exit 2, and the reason MUST be stored in each overwritten record.
- **FR-010a**: **Exit-code precedence**: when a run has both review failures (drift) and problems (broken file/baseline), it MUST exit 2 and print both; the most severe class wins and nothing is hidden.
- **FR-010b**: The failure report's `accept` hint MUST always include `--file`.
- **FR-010c**: A qualified name defined more than once in one file MUST be tracked per definition so a change to any of them is detected. The first definition keeps the existing key (existing baselines remain valid); later ones are keyed `name#2`, `name#3`, … in source order. `init` protects each occurrence separately; `accept` operates per name per file and updates all occurrences, reporting the count (US5).
- **FR-011**: Each of FR-001…FR-010 MUST have at least one automated regression test that **fails on v0.3.0** and passes afterwards; the existing 94 tests MUST remain green.
- **FR-012**: `SyncResult` MUST carry a structured `problems` list (kind, path, line when known, reason) in addition to `failures`, and `is_synchronized` MUST be false when either is non-empty. Per-file and per-baseline problems MUST be returned as data (not raised) so one bad file never stops the run. `init`/`accept` API results MUST likewise expose protected/ambiguous outcomes as data. The API MUST never return a success-shaped result where the CLI would not exit 0. Conditions that prevent any run (missing root) keep raising. All new exceptions derive from one base `PyDocSyncError` carrying an exit-code attribute and MUST NOT inherit from `ValueError`; the CLI maps errors through that base and no longer catches bare `ValueError` (item 10 is fixed here). `InitIncompleteError` carries what was baselined and what was protected; new symbols are still written before it is raised.
- **FR-014**: A successful `check` MUST state its coverage (e.g. "checked 14 files, 212 symbols"), and the API result MUST expose the same counts, so an accidental scan of nothing is visible at a glance.
- **FR-015**: `init --dry-run` MUST write nothing and preview baselined/protected(/overwritten) symbols.
- **FR-021**: A syntactically valid Python file MUST NOT be skipped or reported as a problem because of PyDocSync's own extraction; in particular a class whose body consists only of a docstring MUST be fingerprinted (found during implementation, US2.6).
- **FR-016**: `check` MUST keep passing when code and docs changed together (preserves prior evaluation results), but MUST report every *stale* symbol — stored record differs from current, yet not flagged by `check` — in its output and in `SyncResult.stale`.
- **FR-017**: `check --fail-on-stale` MUST exit 1 with a distinct message when any symbol is stale.
- **FR-018**: A `refresh` command (and `refresh()` API) MUST re-record only stale symbols, require a non-blank reason stored in each record, never touch flagged records or unbaselined symbols, support `--symbol`/`--file`, and print the count.
- **FR-019**: `init` MUST NOT rewrite stale records (a stale record may hide an unreviewed later change); it MUST report them and point to `refresh`. With `--force --reason` they are overwritten like protected records.
- **FR-020**: README and release notes MUST state that, until `refresh` has been run (enforced by `--fail-on-stale`), the tool cannot distinguish a further code-only change from the earlier documented one; 0.4.0 MUST NOT claim to eliminate all silent false passes without that qualification.
- **FR-013**: README, release notes and CLI `--help` MUST describe the new behavior, including the interim workaround for a non-parseable file until `--exclude` ships (move it under a directory that is ignored by default), including the exit-code table (0 synchronized; 1 review required / symbol not found / init protected drift; 2 problems, ambiguity or usage error). The consumer `SKILL.md` is updated only with explicit human permission (its governance rule).

*Key entities*: **Baseline problem** (lockfile path + reason), **Source problem** (file + line + reason), **Ambiguous symbol** (qualname + candidate files).

---

## Success Criteria

- **SC-001**: For each of the 4 reported reproductions, the run no longer ends with "All symbols synchronized" / exit 0.
- **SC-002**: A project with N broken files and M corrupt lockfiles reports all N + M in one run.
- **SC-003**: In the `Command.handle` two-file reproduction, the changed file stays flagged until explicitly accepted with a file selector, and the unchanged file's baseline is never touched.
- **SC-004**: Running `init` after drift leaves `check` failing for the drifted symbol unless the explicit override is used.
- **SC-005**: Zero regressions: all pre-existing tests pass; new regression tests for items 1–4 fail on v0.3.0 and pass on the new version.
- **SC-007**: A run with both drift and a broken file exits 2 and prints both; `SyncResult.problems` lists every problem in one call.
- **SC-008**: Redefined function, property getter/setter and `@overload` cases: a change to any single definition is detected and reported under that definition; `init`'s count matches what is stored; v0.3.0 baselines load without error (duplicated names may need a one-time acknowledgment).
- **SC-009**: Every successful `check` output includes files and symbols checked.
- **SC-010**: The `fee()` three-step reproduction: with `refresh` after step 2, step 3 fails; without it, the stale notice is printed at steps 2 and 3 and `--fail-on-stale` exits 1 at step 2.
- **SC-011**: Existing evaluation suites (specs 002–004) report unchanged precision/recall/churn — stale reporting must not add failures.
- **SC-012**: No bare `ValueError` catch remains in the CLI; a stray `ValueError` from a bug surfaces as a traceback instead of a false "exit 2".
- **SC-006**: No added runtime dependencies; scan time on the repo's own package stays in the same order of magnitude.

---

## Assumptions & Boundaries

**In scope**: items 1–4 of the field report, each with a regression test (the reporter's requested reply); item 10 (via the exception hierarchy, FR-012); and the sticky-baseline bug (US6), added on the reporter's recommendation.

**Out of scope / deferred** (to be recorded in `ideas/future_features.md`; none blocks this spec):
- Item 5 — `init` wording "compliant" vs. counting undocumented symbols.
- Items 6/7 — directory names skipped anywhere in the tree instead of anchored; `node_modules`/`site-packages` not in defaults.
- Item 8 — report paths relative to `--root` only.
- Item 9 — `python -m pydocsync.cli` RuntimeWarning.
- Item 11 — `--exclude` and `check --require-baseline` (exit 2 when no baseline exists, or zero lockfiles while public symbols exist) go to **spec 010, target 0.4.1**, released right after 009. Config file, `--path` and `.pre-commit-hooks.yaml` stay deferred. Interim workaround for a non-parseable file is stated in the 0.4.0 release notes (FR-013).
- Renumbering risk: `name#N` keys are positional. Inserting or removing a definition of a duplicated name shifts later keys and will surface as drift/stale records; this is acceptable (review is required anyway) and is covered in the plan.
- Stale baselines (source file or symbol deleted) are not detected today and are not addressed here.

**Assumptions**:
- Version target `0.4.0`: behavioral CLI change; previously-passing runs may now fail, intentionally.
- The exit code for "cannot evaluate" conditions is a design choice (Q1).

---

## Clarifications

### Resolved (source: end-user field reporter, 2026-09-19)

| Q | Decision | Added details (now requirements) |
|---|---|---|
| Q1 | **A**: exit 2, `PYDOCSYNC ERROR` | Drift + problems together: exit 2, print both (FR-010a). `SyncResult.problems` structured list, not exceptions (FR-012). |
| Q2 | **A**: ambiguity is an error, add `--file` | Ambiguity exit 2, not-found stays exit 1; error prints rerun commands; `PYDOCSYNC001` hint always includes `--file`; same-file duplicates tested (US3, US5, FR-008, FR-010b/c). Module-qualified keys (option B) deferred to a future major version. |
| Q3 | **B**: baseline new, protect drifted, `--force` overrides | `--force` requires `--reason`, stored per overwritten record; exit 1 when any protected; print count and next commands; optional `--dry-run` (FR-010). |

### Resolved (source: project owner decision + end-user testing, 2026-09-19)

| Q | Decision | Notes |
|---|---|---|
| Q4 | **A**: fix same-file duplicates in 009 | Reporter confirmed a redefined function is a real silent pass on 0.3.0. Keying: first definition keeps its key, later ones `name#2`, `name#3`; per-occurrence `init` protection; `accept` per name per file covers all (FR-010c). |
| Q5 | **A**: `--exclude` is spec 010, released as 0.4.1 | 0.4.0 notes state the interim workaround (FR-013). |
| Q6 | **A**: `init --dry-run` in 009; `check --require-baseline` in 010 | Plus a cheap addition in 009: successful `check` states coverage (FR-014). |
| Q7 | **A**: keep `init() -> int`, `accept() -> bool`; typed exceptions carry data; add `init_report()` | Reporter additions: single base `PyDocSyncError` with exit code, not a `ValueError` subclass; `InitIncompleteError` carries baselined + protected data (FR-012). |
| Q8 | **A**: `init` protects only what `check` would flag | Same classifier as `check`. Refined in planning: stale records are left untouched rather than silently overwritten (FR-019). |
| Q9 | **A**: refuse with exit 2 if a file is unparseable and no `--file` | With `--file`, only that file is resolved and read (US3.2). |
| Q10 | Include the sticky-baseline fix in 009 (not split to 011) | Reporter reproduced it (`fee()` case); US6, FR-016…FR-020. |

### Open — owner decision

**Q11 — Default strictness for stale records (US6).**

| Option | Answer | Implications |
|---|---|---|
| A (recommended) | `check` passes with a stale notice by default; `--fail-on-stale` is opt-in for CI; release notes state the residual limit | Preserves the prescribed workflow and existing evaluation results (SC-011); consumers opt in. Step 3 is caught once `refresh` has been run. |
| B | `check` fails (exit 1) on stale by default; `--allow-stale` opt-out | Closes the gap by default, but the documented "update docstring → check → PASS" workflow now requires `refresh` every time, and a `check` with code+doc updates counts as a failure — this collides with the 0.0 % churn evaluation results of specs 003/004. Better candidate for 0.5.0 once `refresh` is established. |

---

## Regression Test Matrix (each MUST fail on v0.3.0 and pass after)

| # | Case | Story |
|---|---|---|
| 1 | Corrupt baseline file (`{ not json`) | US1 |
| 2 | Project whose only file has a syntax error | US2 |
| 3 | Good file beside a broken one; drift still reported; exit 2; both printed | US2 / FR-010a |
| 4 | Two files each with `Command.handle`, one changed (ambiguity exit 2, `--file` works) | US3 |
| 5a | Function defined twice in one file, first definition changed | US5 |
| 5b | Property getter changed (getter's own symbol reported), setter changed | US5 |
| 5c | `@overload` stubs + implementation | US5 |
| 5d | v0.3.0-format baseline passes on unchanged code with duplicates | US5 |
| 6 | `init` after drift (protected, exit 1); `--force` without reason (exit 2); with reason | US4 |
| 7 | Guard cases from spec 008 (new migration; `--root ..`) stay green | regression |
| 8 | `init --dry-run` writes nothing; successful `check` prints file and symbol counts | US4 / FR-014 |
| 9 | `fee()` three steps: step 2 passes with stale notice; after `refresh`, step 3 fails; without `refresh`, notice at 2 and 3; `--fail-on-stale` exit 1 | US6 |
| 10 | `refresh` never touches flagged/new records; blank reason exit 2; docstring-only edit is stale; `init` leaves stale untouched | US6 / US4.9 |
| 11 | `PyDocSyncError` hierarchy: not a `ValueError`; CLI exit codes via the base; stray `ValueError` is not reported as exit 2; `InitIncompleteError` carries baselined + protected | FR-012 |
| 12 | `accept --file` reads only that file (an unparseable sibling does not affect it) | US3.2 / Q9 |
| 13 | File with a docstring-only class is evaluated (init counts it, drift elsewhere in the file is detected) | US2.6 / FR-021 |
