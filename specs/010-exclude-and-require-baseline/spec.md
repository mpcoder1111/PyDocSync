# Feature Specification: 010-exclude-and-require-baseline

## Exclusion Rules (CLI + Config File), Strict-Baseline Mode, Safer Default Ignores, Pre-commit Hook

**Feature Code**: `010-exclude-and-require-baseline`  
**Created**: 2026-09-20  
**Status**: Implemented (decisions taken under owner delegation; see convergence_report.md)  
**Input**: v0.3.0 field report item 11 (no `--exclude`, no config file, no `.pre-commit-hooks.yaml`), items 6/7 (default ignores), and the reporter's `--require-baseline` request (a root with no baseline passes silently). Builds on spec 009, which made unparseable files fail (exit 2) and therefore made an escape hatch necessary.

> **Agent note:** Plan-stage document. Follow `.specify/memory/standards/readme_standards_plan.json`.
> Governance tier: **T3 behavioral** (new CLI flags, new config file, new exit-2 condition). No baseline schema change.
> Design lens chosen by the owner: **the AI coding agent as the primary consumer**.

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Principle IV (no silent skips) drives the visibility requirements |
| 2 | [Design Lens & Decisions](#design-lens--decisions) | Why these choices, from the AI-agent angle; what was cut |
| 3 | [Evidence From Current Code](#evidence-from-current-code) | Today's behavior |
| 4 | [User Scenarios & Testing](#user-scenarios--testing) | US1 `--exclude`, US2 config file, US3 default ignores, US4 `--require-baseline`, US5 visibility, US6 pre-commit hook |
| 5 | [Pattern Syntax](#pattern-syntax) | The exact, strict gitignore-style subset |
| 6 | [Requirements](#requirements) | FR-001 … FR-024 |
| 7 | [Success Criteria](#success-criteria) | Measurable outcomes |
| 8 | [Assumptions & Boundaries](#assumptions--boundaries) | In/out of scope |
| 9 | [Regression Test Matrix](#regression-test-matrix) | Each row must fail on the pre-010 code |

---

## Applicable Constitution Principles

| Principle | Applies? | Notes |
|---|---|---|
| **I. Pure Standard Library Architecture** | **YES** | `re`, `json`, `os`, `pathlib` only. The config file is **JSON** because `tomllib` does not exist on Python 3.10 (the supported floor). |
| **II. Spec-Driven Development** | **YES** | This spec. Spec 009 is committed history; this is a new numbered iteration. |
| **III. Deterministic Representation Synchronization** | **YES** | Pattern matching, discovery order and all reports are deterministic and platform-independent (POSIX-style relative paths, case-sensitive). |
| **IV. Gated Safety & Explicit Review Acknowledgment** | **YES — primary** | Exclusion *reduces* what PyDocSync checks, which is the same class of risk as a silent skip. Every exclusion must therefore be **visible** (counted in the output, unmatched patterns warned about, invalid patterns rejected) and an invalid config must fail loudly. |
| **V. Automated Verification & Scoped Testing** | **YES** | Regression tests that fail on the pre-010 code; full suite stays green. |

---

## Design Lens & Decisions

The owner delegated the open decisions with the instruction to choose what is best **for an AI agent as the consumer**. An agent runs `pydocsync` from memory or from a skill, parses text output, cannot see why a file was skipped, and repeats mistakes silently. That produces these decisions (each can be vetoed):

| # | Decision | Agent-centred reason |
|---|---|---|
| D1 | **`--exclude PATTERN` (repeatable) on `check`, `init`, `accept`, `refresh`.** | One flag, same meaning everywhere, so an agent cannot get different scan sets from different commands. |
| D2 | **Config file `<root>/.pydocsync.json`** with `exclude`, `default_excludes`, `require_baseline`. | An agent typing a bare `pydocsync check` must get the same exclusions as CI. Without persistence every invocation would need remembered flags and a forgotten flag looks like a spurious exit-2 problem. JSON, not TOML, because Python 3.10 has no stdlib TOML reader and behaviour must not depend on the interpreter version. |
| D3 | **Gitignore-style patterns, strict subset** (see Pattern Syntax). Unsupported syntax is an error, never silently reinterpreted. | LLMs know gitignore semantics well, so fewer mistakes; strictness turns the remaining mistakes into immediate, explained failures. |
| D4 | **`--no-default-excludes`** switches off only the *convention* directories (`build`, `dist`, `_archive`, `migrations`, `tests`, `fixtures`). Vendor/cache directories (`venv`, `node_modules`, `site-packages`, `__pycache__`, and any dot-directory) are **always** skipped. | One simple, order-free override that fixes field-report item 6 (real code in `pkg/build/`) with no negation rules to misread. Scanning vendored code is never intended. |
| D5 | **`--include` / negation (`!pattern`) is NOT added.** | Negation makes results order-dependent and is the classic gitignore trap. Cut. |
| D6 | **`check --require-baseline`** (also `require_baseline` in config): exit 2 when no baseline lockfile exists (folder missing or empty) while at least one public symbol exists. | Closes the silent "nothing was ever baselined" pass. In config so agents and CI need not pass the flag. |
| D7 | **Visibility is part of the feature**: `check` reports how many paths the rules excluded; a pattern that matched nothing prints a warning; a mistyped pattern cannot silently do nothing. | The failure mode of exclusion is an agent adding a pattern that hides real code, or a typo that hides nothing. Both must be visible in the output the agent reads. |
| D8 | **`.pre-commit-hooks.yaml`** shipped (one hook, whole-tree check). | The reporter asked; costs one small file. Validated structurally and by running its entry command; **not** executed under the real pre-commit tool (not installed here). |
| D9 | **`--path` (scan only listed files) is NOT added** (backlog). | `check` takes milliseconds on a whole project and `accept --file` / `refresh --file` already scope writes; a second scoping concept every command must honour adds risk for little gain. |
| D10 | **Ships in 0.4.0** together with spec 009 (unreleased). | No user ever sees a release where an unparseable file has no escape hatch. |

---

## Evidence From Current Code

| # | Observation (post-009 code) |
|---|---|
| 1 | `discovery.PathFilter` holds a fixed set of directory **names**, matched at any depth; there is no way to add or remove rules. `discover_python_files(root, path_filter)` accepts a filter, but no CLI/API path builds one. |
| 2 | `DEFAULT_IGNORED_DIRS` = `.venv, venv, .git, __pycache__, build, dist, _archive, migrations, tests, fixtures` (+ any dot-directory). `node_modules` and `site-packages` are absent (item 7). |
| 3 | An unparseable file is a problem (exit 2) since spec 009, so template files that only look like Python have no escape hatch except moving them into an ignored directory. |
| 4 | `accept --file <path>` in an excluded directory returns "Symbol not found in project." (exit 1), which does not say *why*. |
| 5 | A root with no `.project/pydocsync` folder: `check` reports documented symbols as new and passes (exit 0). |
| 6 | The four `run_*` functions each call `discover_python_files(root_dir=root)`; there is one place to thread options through. |

---

## User Scenarios & Testing

### User Story 1 — `--exclude` Removes Files From Every Command (Priority: P1)

As a developer or agent with files that only look like Python (Django/cookiecutter templates, generated code), I want to exclude them by pattern, so `check` neither fails on them nor reports them.

**Independent Test**: Project with a good module and `templates/app.py` containing template syntax; `check --exclude "templates/"`.

**Acceptance Scenarios**:
1. **Given** an unparseable file at `templates/app.py`, **When** `check --exclude "templates/"` runs, **Then** it exits 0, the file is not reported, and the output states the rules excluded 1 path.
2. **Given** the same file without the flag, **Then** `check` exits 2 naming the file (spec 009 behavior unchanged).
3. **Given** `--exclude` given several times, **Then** the union applies.
4. **Given** `init --exclude ...`, **Then** excluded files are never baselined; `refresh` and `accept` (without `--file`) never read them; any existing lockfile of an excluded module is ignored (left on disk untouched).
5. **Given** `accept --file <excluded path>`, **Then** exit 1 with a message that names the excluding rule (e.g. `excluded by pattern 'templates/'`), not the generic "not found".
6. **Given** exclusions that remove every Python file, **Then** exit 2 with the zero-files message stating that exclusions were applied.
7. **Given** the exclude rules change between runs, **Then** no baseline is modified by the change itself.

---

### User Story 2 — Persistent Rules in `.pydocsync.json` (Priority: P1)

As an agent invoking a bare `pydocsync check`, I want the project's exclusions to apply automatically, so I get the same result as CI without remembering flags.

**Independent Test**: `.pydocsync.json` with `{"exclude": ["templates/"]}`, then `pydocsync check` with no flags.

**Acceptance Scenarios**:
1. **Given** `<root>/.pydocsync.json` with `exclude` patterns, **When** any command runs with that `--root`, **Then** the patterns apply exactly as if given via `--exclude`; the file is read from `--root`, not the current directory.
2. **Given** both config and `--exclude`, **Then** the rules are the union (flags add, never remove).
3. **Given** `"default_excludes": false` in config or `--no-default-excludes`, **Then** the convention directories are scanned; vendor/cache directories stay skipped (D4).
4. **Given** `"require_baseline": true`, **Then** `check` behaves as with `--require-baseline` (US4).
5. **Given** a config file that is invalid JSON, not an object, has an unknown key, a wrong value type, or an invalid pattern, **Then** every command exits 2 with a message naming the file and the reason; nothing is scanned or written. (A config that cannot be read must never mean "no exclusions" — that is the corrupt-baseline bug again.)
6. **Given** no config file, **Then** behavior is unchanged.
7. **Given** the Python API, **Then** `check`/`init`/`accept`/`refresh` read the config the same way and accept the same options as keyword arguments.

---

### User Story 3 — Safer Default Ignores (Priority: P1)

As a developer with `node_modules` or a checked-in virtualenv, I want vendored code never scanned; and as a developer with real code in `pkg/build/`, I want a way to scan conventionally-ignored directories.

**Acceptance Scenarios**:
1. **Given** `node_modules/x/y.py` or `site-packages/z.py`, **Then** they are never scanned or baselined (field-report item 7), including when default excludes are disabled.
2. **Given** `pkg/build/core.py` with undocumented public code, **When** `check --no-default-excludes` runs, **Then** it is flagged (item 6); without the flag behavior is unchanged.
3. **Given** `--no-default-excludes`, **Then** `.git`, `__pycache__`, virtualenvs and every dot-directory are still skipped.
4. **Given** `DEFAULT_IGNORED_DIRS` (existing public constant), **Then** it still contains all previous names and now also `node_modules` and `site-packages`.

---

### User Story 4 — `check --require-baseline` (Priority: P1)

As a CI owner or agent, I want `check` to fail when no baseline exists, so "nothing was ever baselined" cannot look like success.

**Acceptance Scenarios**:
1. **Given** a root with no `.project/pydocsync` folder, **When** `check --require-baseline` runs, **Then** exit 2, message says no baseline exists and to run `pydocsync init`; `SyncResult.problems` carries a `BASELINE_MISSING` problem.
2. **Given** the folder exists but contains zero lockfiles while at least one **public** symbol exists, **Then** same outcome.
3. **Given** at least one lockfile exists, **Then** the flag adds nothing (a module never baselined still follows the normal new-symbol rules).
4. **Given** the flag on a project with no public symbols and no baseline, **Then** it passes.
5. **Given** the flag together with drift or other problems, **Then** exit 2 wins and everything is printed (spec 009 precedence).
6. **Given** no flag (and `require_baseline` unset), **Then** behavior is unchanged.

---

### User Story 5 — Exclusions Are Always Visible (Priority: P1, agent-critical)

As an agent, I cannot see files that were skipped, so the output must tell me what the rules did.

**Acceptance Scenarios**:
1. **Given** any `check` run where user rules (flags or config) excluded something, **Then** the output includes `PYDOCSYNC: excluded by rules: N path(s).` after the coverage line; nothing extra is printed when no rule applied. The existing lines (`All symbols synchronized with baseline.`, `checked N files, M symbols.`) are unchanged.
2. **Given** a pattern that matched no path during discovery, **Then** a warning `PYDOCSYNC WARNING: exclude pattern 'X' (from --exclude|.pydocsync.json) matched no path.` goes to stderr; the exit code is unaffected.
3. **Given** `SyncResult`, **Then** it exposes `excluded_count` and `unmatched_excludes`.
4. **Given** an invalid pattern (empty, negation, backslash, character class, `***`, ...), **Then** exit 2 with a message that quotes the pattern and states the supported syntax (agents self-correct from the message).

---

### User Story 6 — Pre-commit Hook (Priority: P2)

As a team using `pre-commit`, I want a ready-made hook so I do not write a wrapper script.

**Acceptance Scenarios**:
1. **Given** `.pre-commit-hooks.yaml` at the repository root, **Then** it defines hook `pydocsync-check` with `entry: pydocsync check`, `language: python`, `types: [python]`, `pass_filenames: false`.
2. **Given** the hook's `entry`, **When** executed in a temp project, **Then** it behaves exactly like `pydocsync check` (same exit codes).
3. **Given** the manifest, **Then** users can add arguments (`--fail-on-stale`, `--require-baseline`, `--exclude`) via the standard `args:` key without editing the hook.

---

### Edge Cases

- Patterns use POSIX separators on every platform; a pattern containing `\` is rejected (message: use `/`).
- Matching is case-sensitive on every platform.
- A pattern matching a directory excludes everything beneath it without descending (pruning; performance preserved).
- `--root ..` and relative roots: patterns and the config are relative to the resolved root.
- `.pydocsync.json` is not a `.py` file and is never scanned; a config in a parent of `--root` is not consulted.
- Duplicate patterns are harmless; the unmatched warning is emitted once per distinct pattern.
- An unmatched-pattern warning does not fire for a pattern whose matches lie only inside directories the default rules already prune (they are never visited); the message says "matched no scanned path".
- `--exclude` / config affect discovery only; baseline lockfiles are never deleted or rewritten because of an exclusion.
- Exclusion counts count *paths pruned or filtered* (a pruned directory counts once), not files inside it.

---

## Pattern Syntax

A strict, documented subset of gitignore. Patterns are matched against the **POSIX-style path relative to the root** of each directory and each `.py` file visited.

| Form | Meaning | Example |
|---|---|---|
| `name` (no `/`) | Any file or directory with this name at any depth | `generated` |
| `name/` | Any **directory** with this name at any depth | `templates/` |
| `a/b` or `/a/b` (contains an inner or leading `/`) | Anchored to the root (path must equal `a/b`) | `pkg/legacy` |
| `a/b/` | Anchored directory | `pkg/legacy/` |
| `*` | Any characters except `/` | `*_pb2.py` |
| `?` | One character except `/` | `mod?.py` |
| `**` as a whole segment | Zero or more directories | `pkg/**/gen`, `**/tmp`, `pkg/**` |

A pattern that matches a directory excludes the directory and everything beneath it. **Not supported and rejected with an error**: empty patterns, a leading `!` (negation), `\`, `[` `]` character classes, `**` embedded inside a segment (`a**b`, `***`), a leading `#`. Leading/trailing whitespace is an error, not trimmed. Rejection is deliberate: a pattern that means something different from what the author wrote is a silent skip.

---

## Requirements

- **FR-001**: `check`, `init`, `accept` and `refresh` MUST accept `--exclude PATTERN` (repeatable) and apply it during discovery.
- **FR-002**: Patterns MUST follow the Pattern Syntax above, be deterministic and platform-independent, and be validated before any scan or write; an invalid pattern MUST exit 2 (`InvalidArgumentError`) naming the pattern and the reason.
- **FR-003**: A directory matched by a pattern MUST be pruned without descending into it.
- **FR-004**: Excluded files MUST NOT be scanned, reported, baselined, refreshed or accepted; their existing lockfiles MUST be left untouched and ignored.
- **FR-005**: `accept --file <excluded path>` MUST exit 1 and state which rule excludes the file (exclusion by a user pattern, by config, or by a default directory).
- **FR-006**: If exclusions remove every Python file, the run MUST exit 2 with the zero-files error, stating that exclusions were applied.
- **FR-007**: The tool MUST read `<root>/.pydocsync.json` when present, with keys `exclude` (list of strings), `default_excludes` (boolean, default true) and `require_baseline` (boolean, default false). Unknown keys, wrong types, invalid JSON, a non-object root or an invalid pattern MUST raise a `ConfigError` (a `PyDocSyncError`, exit 2) naming the file and reason. A missing file MUST mean "no config".
- **FR-008**: Effective rules MUST be the union of config `exclude` and `--exclude` flags. `--no-default-excludes` or `"default_excludes": false` disables the convention directories only; `--require-baseline` or `"require_baseline": true` enables US4.
- **FR-009**: Vendor/cache directories (`venv`, `node_modules`, `site-packages`, `__pycache__`, and every dot-directory) MUST always be skipped. `DEFAULT_IGNORED_DIRS` MUST remain a superset of its 0.3.0 value and include `node_modules` and `site-packages`. Convention directories (`build`, `dist`, `_archive`, `migrations`, `tests`, `fixtures`) are skipped by default and scanned with `--no-default-excludes`.
- **FR-010**: `check --require-baseline` MUST emit a `BASELINE_MISSING` problem (exit 2) when the baseline folder is absent or contains no lockfile **and** at least one public symbol was found; it MUST NOT alter behavior otherwise (in particular a project with no public symbols passes).
- **FR-011**: When user rules excluded anything, `check` MUST print `PYDOCSYNC: excluded by rules: N path(s).` after the coverage line; existing output lines MUST be unchanged.
- **FR-012**: A pattern that matched no visited path MUST produce a stderr warning naming the pattern and its source; it MUST NOT change the exit code.
- **FR-013**: `SyncResult` MUST expose `excluded_count: int` and `unmatched_excludes: list[str]`. The Python API (`check`, `init`, `init_report`, `accept`, `refresh`) MUST accept `exclude`, `default_excludes` and (for `check`) `require_baseline` keyword arguments and MUST read the config file by default.
- **FR-014**: `.pre-commit-hooks.yaml` MUST define hook `pydocsync-check` (`entry: pydocsync check`, `language: python`, `types: [python]`, `pass_filenames: false`).
- **FR-015**: Existing behavior without any of the new flags/config MUST be byte-identical apart from the default-ignore additions (FR-009): the pre-010 test suite (153 tests) MUST stay green.
- **FR-016**: Each of FR-001…FR-014 MUST have at least one regression test that **fails on the pre-010 code** (the committed spec-009 state) and passes afterwards.
- **FR-017**: README, `--help` texts and the consumer `SKILL.md` MUST document the rules, the config file, the exit-code effects, and the agent guardrail: exclusions are for non-Python, generated or vendored files; excluding real source to make `check` pass is not an acceptable fix, and every exclusion appears in the output.
- **FR-018**: No new runtime dependency; scan performance on the repository's own package stays within the same order of magnitude (existing 200 ms budget test).
- **FR-019**: `init --dry-run` MUST honour exclusions (preview equals real run).
- **FR-020**: The README "Upgrading to 0.4.0" section and version references MUST be updated: this ships in 0.4.0 (no 0.4.1 statement remains).
- **FR-021**: `--require-baseline` failures MUST print the concrete next step (`pydocsync init`).
- **FR-022**: Config and flag help text MUST show the exact pattern syntax examples (agents read `--help`).
- **FR-023**: `refresh --file`/`accept --file` MUST use the same exclusion evaluation as discovery (single implementation).
- **FR-025** *(added during implementation)*: The `accept` / `refresh` commands suggested by reports MUST carry `--no-default-excludes` when the run used it, so the suggestion is accepted as written.
- **FR-024**: Error and warning messages introduced here MUST be single-purpose lines that name the source (`--exclude`, `.pydocsync.json`) so an agent can fix the right place.

*Key entities*: **Exclusion rule** (pattern + source), **Settings** (effective exclude list, default_excludes, require_baseline), **Discovery result** (files, excluded count, unmatched patterns).

---

## Success Criteria

- **SC-001**: The reporter's template-file scenario (unparseable `templates/*.py`) goes from a permanent exit 2 to exit 0 with one `--exclude` flag or one config line, and the output says what was excluded.
- **SC-002**: A bare `pydocsync check` in a project with `.pydocsync.json` gives exactly the result of the equivalent flags (byte-identical output).
- **SC-003**: An invalid pattern or invalid config never results in a scan: 100 % of the invalid-input cases in the matrix exit 2 with a message naming the offending input.
- **SC-004**: `check --require-baseline` on a never-baselined project (with public symbols) exits 2; adding a baseline makes it pass.
- **SC-005**: Zero regressions: the 153 pre-existing tests pass; new regression tests fail on the spec-009 commit and pass now.
- **SC-006**: A typo'd pattern (matching nothing) is reported by a warning in 100 % of cases in the matrix.
- **SC-007**: No new runtime dependency; the 200 ms package-scan budget test still passes.

---

## Assumptions & Boundaries

**In scope**: US1–US6 above.

**Out of scope / backlog** (recorded in `ideas/future_features.md`):
- `--path` scan-subset option (D9) and `--include`/negation patterns (D5).
- TOML / `pyproject.toml` config, `--config PATH`, nested per-directory configs, environment-variable config.
- Item 8 (report paths relative to `--root` only), item 5 (init wording), item 9 (`RuntimeWarning`).
- Real-tool execution of the pre-commit hook.

**Assumptions**:
- Case-sensitive matching on all platforms is acceptable (documented).
- `.pydocsync.json` next to the code root is the only config location.
- The pre-commit manifest schema (`id`, `name`, `entry`, `language`, `types`, `pass_filenames`, `description`) is stable; it is validated structurally only.

---

## Regression Test Matrix

Each row must fail on the committed spec-009 code (except guards marked *guard*).

| # | Case | Story |
|---|---|---|
| 1 | Unparseable `templates/app.py` + `--exclude "templates/"` → exit 0, `excluded by rules: 1 path(s)` | US1 |
| 2 | Same file without flag → exit 2 (*guard*) | US1 |
| 3 | Repeated `--exclude`; unions | US1 |
| 4 | `init`/`refresh`/`accept` ignore excluded files; existing lockfile left byte-identical | US1 |
| 5 | `accept --file <excluded>` exit 1 naming the rule | US1 / FR-005 |
| 6 | All files excluded → exit 2 zero-files message mentions exclusions | US1 |
| 7 | Pattern table: `name`, `name/`, anchored, leading `/`, `*`, `?`, `**` (start/middle/end), files vs dirs, deep paths, no partial-name matches, case-sensitivity | Pattern Syntax |
| 8 | Invalid patterns (empty, `!x`, `a\b`, `[x]`, `a**b`, `#x`, padded whitespace) → exit 2, message quotes the pattern | FR-002 |
| 9 | Config file drives a bare `check` (same output as flags); config read from `--root`, not cwd | US2 |
| 10 | Config errors: invalid JSON, non-object, unknown key, wrong type, invalid pattern → exit 2 naming `.pydocsync.json`; missing file = no config (*guard*) | US2 / FR-007 |
| 11 | Config + flags union; `--no-default-excludes` and `default_excludes: false` | US2/US3 |
| 12 | `node_modules/` and `site-packages/` skipped (even with `--no-default-excludes`); `pkg/build/` flagged with `--no-default-excludes`; dot-dirs/`__pycache__` still skipped; `DEFAULT_IGNORED_DIRS` superset | US3 |
| 13 | `--require-baseline`: no folder → exit 2 `BASELINE_MISSING`; empty folder + public symbols → exit 2; with a lockfile → pass; no public symbols → pass; config `require_baseline`; with drift → exit 2 both printed; message names `pydocsync init` | US4 |
| 14 | Unmatched pattern → stderr warning, exit code unchanged; warning names source | US5 |
| 15 | `SyncResult.excluded_count` / `unmatched_excludes`; API keyword arguments; API reads config | FR-013 |
| 16 | `init --dry-run` honours exclusions | FR-019 |
| 17 | `.pre-commit-hooks.yaml` keys present; entry command runs like `check` | US6 |
| 18 | Output lines from 009 unchanged when no rules apply (*guard*) | FR-011/FR-015 |
