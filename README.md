# PyDocSync

**Deterministic Code–Documentation Synchronization for AI-Assisted Python Development**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python: >=3.10](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Status: Experimental 0.4.0](https://img.shields.io/badge/Status-Experimental_0.4.0-orange.svg)]()

> **PyDocSync deterministically detects when Python implementation changes may require corresponding documentation updates or an explicit documentation review.**

PyDocSync is designed for **AI-assisted / agentic coding workflows**. It does not attempt to prove that natural-language documentation is semantically correct.

---

## The Problem

An AI coding agent can modify working Python code, pass tests, and still leave documentation describing the previous implementation.

For example:

```python
def parse_config(path, timeout=30):
    """Parse configuration using the configured timeout."""
```

An AI agent changes the implementation to:

```python
def parse_config(path, timeout=60):
    """Parse configuration using the configured timeout."""
```

The code may be valid. Tests may pass. Type checking may pass.

But the documentation may now be stale.

PyDocSync adds a deterministic check to catch this maintenance gap:

```text
KNOWN INITIAL STATE
       │
       ▼
 pydocsync init
       │
       ▼
   BASELINE
       │
       │
       │   AI agent / developer modifies code
       ▼
 pydocsync check
       │
       ▼
Implementation representation changed
while related documentation did not
       │
       ▼
 PYDOCSYNC001
       │
       ▼
Documentation must be updated
OR the change must be explicitly reviewed
       │
       ▼
      PASS
```

The goal is **not simply to detect that code changed**.

The goal is to deterministically identify changes that may create a **documentation-review obligation**.

---

## Three Layers of Documentation Maintenance

PyDocSync complements established Python quality tools:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Layer A — Missing Information                                               │
│                                                                             │
│ Missing docstrings, missing type annotations, missing Args/Returns, etc.    │
│                                                                             │
│ Typical tools: Ruff / pydocstyle / pydoclint                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer B — Contract / Signature Drift                                        │
│                                                                             │
│ Function signatures, parameter names, types, Returns, Raises, etc.         │
│ no longer agree with documentation.                                         │
│                                                                             │
│ Typical tools: Mypy / Pyright / pydoclint                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Layer C — Implementation ↔ Documentation Drift                              │
│                                                                             │
│ Implementation changes while related documentation remains unchanged,       │
│ even when the API/type signature may still appear valid.                    │
│                                                                             │
│ PyDocSync's focus                                                      ✓    │
└─────────────────────────────────────────────────────────────────────────────┘
```

**PyDocSync does not replace Ruff, Mypy, Pyright, pydoclint, or pytest.**

It adds a deterministic synchronization signal for **Layer C**.

---

## How PyDocSync Works

PyDocSync analyzes Python source using the AST and creates separate deterministic SHA-256 fingerprints for different representations of the same function/class.

```text
                         PYTHON SOURCE
                              │
                              ▼
                     ┌─────────────────┐
                     │   AST Analysis  │
                     └────────┬────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
       CODE / API          TYPE / DOC        RAISE / EXAMPLE
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    SHA-256 fingerprints
                              │
                              ▼
                   Versioned baseline state
                              │
                    AI modifies Python code
                              │
                              ▼
                     pydocsync check
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
               PASS                   PYDOCSYNC001
                                           │
                                  Documentation review
                                           │
                         ┌─────────────────┴─────────────────┐
                         ▼                                   ▼
                  Update documentation              Existing documentation
                         │                            is still accurate
                         │                                   │
                         │                            pydocsync accept
                         │                                   │
                         └─────────────────┬─────────────────┘
                                           ▼
                                  pydocsync check
                                           │
                                           ▼
                                         PASS
```

### Seven Representation Planes

The current implementation maintains independent fingerprints for:

```text
CODE
API
TYPE
DOC
RAISE_TYPE
RAISE_DETAIL
EXAMPLE
```

For example, if an AI agent changes a default value and adds a new exception:

```text
BEFORE                       AFTER

CODE          AAAAA          CODE          XXXXX  ← changed
API           BBBBB          API           YYYYY  ← changed
TYPE          CCCCC          TYPE          CCCCC  ← unchanged
DOC           DDDDD          DOC           DDDDD  ← unchanged
RAISE_TYPE    EEEEE          RAISE_TYPE    ZZZZZ  ← changed
```

PyDocSync can therefore provide evidence about **what changed and what related representation did not change**, rather than relying on one opaque whole-function hash.

---

## Deterministic Review, Not Semantic Proof

A fingerprint can deterministically establish that a representation changed.

It cannot prove that a natural-language statement is true.

For example, a hash cannot prove whether:

> "Retries three times before raising an error."

is semantically correct.

Therefore PyDocSync treats a mismatch as a **documentation-review obligation** rather than automatically declaring the documentation incorrect.

When deterministic static analysis cannot safely establish the impact of a change, PyDocSync routes the case to:

```text
UNKNOWN
review_required = True
```

This is intentional: **PyDocSync prefers an explicit review over silently allowing potentially stale documentation.**

---

## Installation

PyDocSync 0.4.0 is an experimental release.

Install directly from GitHub:

```bash
python -m pip install git+https://github.com/mpcoder1111/PyDocSync.git
```

For the `v0.4.0` release tag:

```bash
python -m pip install git+https://github.com/mpcoder1111/PyDocSync.git@v0.4.0
```

A release wheel is also available:

```bash
python -m pip install pydocsync-0.4.0-py3-none-any.whl
```

### Requirements

- Python **3.10 or newer**
- Zero external runtime dependencies (pure standard library)
- Explicitly exercised on Python 3.10, 3.11, 3.12, and 3.13

---

## Quick Start

Run the commands from your Python project root.

### 1. Establish the Initial Baseline

```bash
pydocsync init
```

This creates local baseline state under `.project/pydocsync/`.

The baseline represents the known code/documentation state **before future modifications are checked**.

> [!IMPORTANT]
> Do **not** run `pydocsync init` after every AI modification. The purpose of the baseline is to preserve the state against which subsequent modifications are detected.

`init` is safe to run again when you add a new module: it baselines **new** symbols only. A record that `pydocsync check` currently flags is **protected** — left untouched, listed, and `init` exits `1` — so running `init` can never silently erase drift. To deliberately reset such records, use `pydocsync init --force --reason "<why>"` (the reason is stored in each overwritten record). `pydocsync init --dry-run` previews what would be baselined and protected without writing anything.

### 2. Check the Project

```bash
pydocsync check
```

If the monitored representations are synchronized, it exits with `0` (`PASS`).

### 3. AI Agent Modifies Code

Suppose an AI agent changes:

```python
def parse_config(path, timeout=30):
    """Parse configuration using the configured timeout."""
```

to:

```python
def parse_config(path, timeout=60):
    """Parse configuration using the configured timeout."""
```

The AI agent has modified the **code**, but has not modified the **documentation**.

### 4. Run PyDocSync

```bash
pydocsync check
```

PyDocSync emits a structured diagnostic:

```text
======================================================================
PYDOCSYNC001: 1 symbol(s) require documentation review.
======================================================================

Symbol:     parse_config
File:       src/parser.py:3
Impact:     HIGH_IMPACT
Rule ID:    RULE_DEFAULT_VALUE_CHANGE
Changed:    api, code
Evidence:   defaults changed: ['30'] -> ['60']
Reason:     Default parameter value altered in function signature.
Action:     Update docstring for 'parse_config', or if documentation
            remains 100% accurate, acknowledge via:
            pydocsync accept --symbol parse_config --reason "<audit reason>"
----------------------------------------------------------------------
```

The command returns exit code `1`.

### 5. Update Documentation When Required

If the implementation change affects documented behavior, update the docstring/documentation and run `pydocsync check` again to return to `PASS`.

### 6. Explicitly Accept a Reviewed Change

Sometimes an implementation change is intentional but the existing documentation remains completely accurate (e.g. an internal refactoring or performance optimization).

After reviewing the documentation:

```bash
pydocsync accept --symbol parse_config --reason "Increased default timeout to 60s for high-latency connections; public doc remains accurate."
```

Then `pydocsync check` returns to the clean `PASS` state (exit code `0`).

If the same qualified name exists in more than one file (for example `Command.handle` in several Django apps), `accept` refuses to guess (exit code `2`), lists every candidate and prints the exact command to re-run with `--file`:

```bash
pydocsync accept --symbol Command.handle --reason "<audit reason>" --file app/a/commands.py
```

The `PYDOCSYNC001` report always includes `--file` in its suggested command. A name that is defined more than once **inside one file** (redefinitions, `@overload`, property getter and setter) is tracked per definition (`name`, `name#2`, ...); `accept` covers all of them and reports how many it updated.

> [!NOTE]
> **Trust and Authorization Model**:  
> `pydocsync accept` does **not** prove documentation correctness. It serves as an audit record that a human developer or AI agent has reviewed the change and determined the existing doc remains accurate. Non-empty, descriptive audit reasons are strictly required.

### After a Documented Change: Stale Baselines and `refresh`

When code **and** its docstring change together, `pydocsync check` passes (correct: the documentation was updated). But the stored baseline still describes the old code and docstring, so it can no longer guard the next code-only change. `check` therefore reports these symbols:

```text
PYDOCSYNC: 1 symbol(s) have updated documentation not yet recorded in the baseline.
  fee.py: fee (changed: code, doc)
  Record them with: pydocsync refresh --reason "<why the docs match the code>"
```

```bash
pydocsync refresh --reason "Fee raised to 8 percent; docstring updated"
```

`refresh` re-records **only** these stale symbols (optionally narrowed with `--symbol` / `--file`). It never touches a record that `check` flags, and never baselines new symbols. Use `pydocsync check --fail-on-stale` in CI to fail (exit `1`) until the baseline is refreshed.

> [!WARNING]
> **Known limit.** Until `refresh` has been run, PyDocSync cannot tell a *further* code-only change from the earlier documented one, because both differ from the old baseline in code and docs. The notice is printed on every `check`, and `--fail-on-stale` makes it enforceable; without them, a symbol in this state is not fully guarded.

### Nothing Is Skipped Silently

PyDocSync never reports "synchronized" for something it could not evaluate. These are reported as **problems** and make `check` exit `2` (all of them, in one run, together with any drift):

- a baseline lockfile that is unreadable, empty, not valid JSON, structurally invalid, or written by a newer schema version;
- a Python file that cannot be read or decoded (UTF-8) or parsed, e.g. `SyntaxError line 12: ...` (also when a file uses syntax that your interpreter version does not support).

A module that was simply never baselined is not a problem. A successful run states what it covered (`checked 14 files, 212 symbols`). From Python, `check()` returns problems in `SyncResult.problems` instead of raising.

If a file is intentionally not parseable (for example template files that look like Python), exclude it (see [Excluding Files](#excluding-files)).

### Default Ignored Directories

PyDocSync prunes these directories at any depth during traversal:

```text
Always skipped (vendor/cache):  venv, node_modules, site-packages, __pycache__, and every dot-directory (.git, .venv, ...)
Skipped by default:             build, dist, _archive, migrations, tests, fixtures
```

Real code that lives in a conventionally ignored directory (for example `pkg/build/`) can be checked with `--no-default-excludes` (or `"default_excludes": false` in the config file). That switches off only the second group; vendor/cache directories are never scanned.

### Excluding Files

For files that only *look* like Python (Django/cookiecutter templates, generated code), exclude them instead of moving them:

```bash
pydocsync check --exclude "templates/" --exclude "**/*_pb2.py"
```

`--exclude PATTERN` (repeatable) works the same on `check`, `init`, `accept` and `refresh`. To make it permanent, put the patterns in `<root>/.pydocsync.json`, which every command reads automatically (from `--root`, not from the current directory), so a bare `pydocsync check` gives the same result as your CI:

```json
{
  "exclude": ["templates/", "**/*_pb2.py", "pkg/generated/**"],
  "default_excludes": true,
  "require_baseline": false
}
```

All keys are optional; unknown keys or wrong types are an error (exit `2`), never silently ignored. Flags **add** to the config's patterns; nothing on the command line removes a config rule.

**Pattern syntax** (a strict subset of gitignore, matched against the POSIX-style path relative to the root, case-sensitive):

| Pattern | Matches |
|---|---|
| `generated` | any file or directory named `generated`, at any depth |
| `templates/` | directories named `templates` (trailing `/` = directories only) |
| `pkg/legacy` or `/pkg/legacy` | exactly that path from the root (a `/` inside the pattern anchors it) |
| `*_pb2.py`, `mod?.py` | `*` = any characters except `/`, `?` = one character |
| `pkg/**/gen`, `**/tmp`, `pkg/**` | `**` as a whole segment = zero or more directories (`pkg/**` = everything beneath `pkg`) |

A pattern that matches a directory excludes everything beneath it. Anything else is **rejected with an error** (exit `2`) that quotes the pattern, rather than being reinterpreted: negation (`!x`), backslashes, `[..]`, `a**b`, `#x`, empty or whitespace-padded patterns, `.`/`..`.

**Exclusions are always visible.** `check` prints `PYDOCSYNC: excluded by rules: N path(s).` whenever your rules removed something, and a pattern that matched nothing (usually a typo) produces `PYDOCSYNC WARNING: exclude pattern 'x' (from --exclude) matched no scanned path.` on stderr. `accept --file` on an excluded file says which rule excludes it.

> [!WARNING]
> Excluding real source code just to make `check` pass defeats the tool. Use exclusions for non-Python, generated or vendored files, and review them like any other change.

### Strict Baseline Mode

By default a project that was never baselined passes `check` (its documented symbols count as new). To make that an error, use `pydocsync check --require-baseline` (or `"require_baseline": true` in the config): if no baseline lockfile exists while the project has public symbols, `check` exits `2` with `BASELINE_MISSING` and tells you to run `pydocsync init`.

### pre-commit

```yaml
repos:
  - repo: https://github.com/mpcoder1111/PyDocSync
    rev: v0.4.0
    hooks:
      - id: pydocsync-check
        args: [--fail-on-stale, --require-baseline]   # optional
```

The hook (`.pre-commit-hooks.yaml`) runs `pydocsync check` on the whole project whenever Python files change (`pass_filenames: false`). It has been verified by running its entry command; it has not been executed under the pre-commit tool itself.

### CLI Command Reference

Every command scans from `--root` (default `.`), reads `<root>/.pydocsync.json` if present, and accepts `--exclude PATTERN` (repeatable) and `--no-default-excludes`. `pydocsync --help` shows the workflow and exit codes; `pydocsync <command> --help` shows options and examples; `pydocsync --version` prints the version.

| Command | What it does | Options and examples |
|---|---|---|
| `pydocsync check` | Compares the code with the baseline. Prints `PYDOCSYNC001` for symbols needing review, `checked N files, M symbols` on success, a notice for stale baselines, and what your exclusions removed. | `--fail-on-stale` (exit 1 on stale baselines), `--require-baseline` (exit 2 if no baseline exists). CI: `pydocsync check --fail-on-stale --require-baseline` |
| `pydocsync init` | Baselines symbols that have no record yet (onboarding a module). Records that `check` flags are **protected**; stale records are left for `refresh`. | `--dry-run` (preview), `--force --reason "<why>"` (deliberate reset). `pydocsync init --dry-run` |
| `pydocsync accept` | Records that you reviewed a flagged symbol and its documentation is still accurate. | `--symbol NAME --reason "<why>"` (both required), `--file PATH` (required if the name exists in several files; the `PYDOCSYNC001` hint includes it). `pydocsync accept --symbol Command.handle --reason "reviewed" --file app/commands.py` |
| `pydocsync refresh` | Records baselines whose docstring was updated together with the code (the stale notice). Never touches flagged records or new symbols. | `--reason "<why>"` (required), `--symbol NAME`, `--file PATH`. `pydocsync refresh --reason "docs updated with the code"` |

### CLI Exit Codes

| Exit Code | Classification | Condition |
|---|---|---|
| **`0`** | `PASS` | All monitored symbols synchronized with baseline (a stale-baseline notice may be printed). |
| **`1`** | `PYDOCSYNC001` | Review obligation detected (code changed without doc update), `accept` symbol not found or `accept --file` on an excluded file, `init` protected drifted records, or stale baseline with `check --fail-on-stale` (`PYDOCSYNC003`). |
| **`2`** | `ERROR` | A problem prevented a complete evaluation (corrupt baseline, unreadable/unparseable file), ambiguous `accept` symbol, invalid `--exclude` pattern or `.pydocsync.json`, `check --require-baseline` with no baseline (`BASELINE_MISSING`), CLI usage error, missing or blank audit reason, or zero Python source files found (also when the exclusion rules removed them all). When a run has both drift and problems, exit `2` wins and both are printed. |

---

## How AI Agents Use PyDocSync

PyDocSync does not need to be part of the AI model itself. It serves as a deterministic verification step in the AI agent's coding workflow:

```text
                         AI CODING AGENT
                                │
                                │ modifies code
                                ▼
                    ┌────────────────────────┐
                    │ Tests / Lint / Types   │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │    pydocsync check     │
                    └────────────┬───────────┘
                                 │
                       ┌─────────┴─────────┐
                       ▼                   ▼
                     PASS             PYDOCSYNC001
                                           │
                                    AI reviews signal
                                           │
                           ┌───────────────┴──────────────┐
                           ▼                              ▼
                    Update documentation        Documentation still
                           │                     accurate
                           │                              │
                           │                       pydocsync accept
                           │                              │
                           └──────────────┬───────────────┘
                                          ▼
                                  pydocsync check
                                          │
                                          ▼
                                         PASS
```

Other outcomes: exit `2` means part of the project was **not** checked (corrupt baseline, unparseable file, missing baseline with `--require-baseline`, ambiguous `accept`, invalid `--exclude`/config), so fix that first. `PASS` with a *stale-baseline notice* means docs were updated together with the code: run `pydocsync refresh --reason "..."`. Files that only look like Python (templates, generated code) are handled with `--exclude` / `.pydocsync.json`, never by deleting or editing them.

---

## Programmatic Python API

PyDocSync provides a minimal, typed Python API for tool builders and IDE extensions:

```python
from pydocsync import check, init, accept, refresh, SyncResult, SyncFailure

# Scan working tree
result = check(root_dir=".")

if not result.is_synchronized:
    print(f"Detected {result.failure_count} review obligations:")
    for failure in result.failures:
        print(f"  - {failure.symbol.qualname}: {failure.rule_result.reason}")
    for problem in result.problems:  # unreadable files / corrupt baselines, never dropped
        print(f"  ! {problem.kind.value} {problem.path}:{problem.line} {problem.reason}")
print(f"checked {result.files_checked} files, {result.symbols_checked} symbols; stale: {len(result.stale)}")

# Programmatically acknowledge a reviewed symbol
accept(
    symbol_qualname="mypkg.func",
    reason="Refactored internal algorithm; verified documentation remains accurate.",
    root_dir=".",
    file="mypkg/module.py",  # required when the name exists in several files
)
```

`init()` and `accept()` keep their simple return types and raise a typed error whenever the CLI would not exit `0`. All errors derive from `PyDocSyncError` (which has an `exit_code` and is deliberately **not** a `ValueError`): `AmbiguousSymbolError` (carries the candidate files), `InitIncompleteError` (carries an `InitResult` with what was baselined and what was protected — new symbols are written first), `SourceProblemsError`. To get the same data without an exception use `init_report(root_dir, dry_run=True)`.

### Supported Public API Surface

The stable public interface consists strictly of:
- `check(root_dir=".", *, exclude=(), default_excludes=None, require_baseline=None) -> SyncResult` (with `problems`, `stale`, `files_checked`, `symbols_checked`, `excluded_count`, `unmatched_excludes`); `init`, `init_report`, `accept` and `refresh` take the same `exclude` / `default_excludes` keyword arguments, and all of them read `.pydocsync.json` from `root_dir`
- `init(root_dir=".", *, force=False, reason=None) -> int` and `init_report(root_dir=".", *, force=False, reason=None, dry_run=False) -> InitResult`
- `accept(symbol_qualname, reason, root_dir=".", *, file=None) -> bool`
- `refresh(root_dir=".", *, reason, symbol=None, file=None) -> int`
- `SyncResult`, `SyncFailure`, `Problem`, `ProblemKind`, `StaleRecord`, `InitResult`, `SymbolRef`
- `PyDocSyncError`, `AmbiguousSymbolError`, `ConfigError`, `FileExcludedError`, `InitIncompleteError`, `InvalidArgumentError`, `SourceProblemsError`
- `__version__`

*Internal implementation modules (`ast_extract`, `fingerprint`, `classifier`, `baseline`, `report`) are private and subject to change.*

---

## Monitored Symbol Policy

By default, PyDocSync monitors:
- **Public Callables**: Top-level functions and class methods not prefixed with `_`.
- **Public Classes**: Top-level classes not prefixed with `_`.

Common non-source/build directories are excluded by default:
```text
tests/
.venv/
__pycache__/
dist/
build/
```

---

## Baseline State & Schema Versioning

PyDocSync stores versioned synchronization state under `.project/pydocsync/`:

```json
{
  "schema_version": 1,
  "pydocsync_version": "0.2.0",
  "fingerprint_algorithm": "sha256",
  "symbols": { ... }
}
```

The baseline is **not a replacement for Git**. Git provides source history and commits; PyDocSync provides normalized representation fingerprints, change classification, and audit records.

---

## External Evaluation Corpora

PyDocSync was evaluated against three unrelated open-source Python projects:
- **Dulwich** — Git engine / protocol and binary parsing code.
- **Janome** — Morphological NLP / tokenizer and dictionary trie code.
- **python-sdb** — Binary serialization and bitwise structure parsing code.

> [!NOTE]
> These projects were used **only as external evaluation corpora**. They are not dependencies, are not bundled in PyDocSync, and received zero project-specific classifier rules.

---

## Empirical Benchmark Results (Observed Metrics)

The following are **observed benchmark metrics**, not claims of universal accuracy:

### 1. Adversarial Stress Testing
- 16 adversarial attack cases under dual execution.
- Addressed evaluation-order and dictionary-key-order blind spots; cataloged heap aliasing as an AST boundary.

### 2. Real-Project Evaluation (67 Symbols, 15 Scenarios)
- Evaluated against production code with dual blind human reviewer consensus (Reviewer A & B).
- **Observed review-trigger recall: 100.0% (11/11).**
- **Observed review-trigger precision: 78.6%.**
- **Unnecessary documentation churn: 0.0%.**
- **Full-package scan time: 49.97 ms.**

### 3. External Multi-Repository Evaluation (61 Symbols, 20 Scenarios)
- Evaluated across Dulwich, Janome, and python-sdb with frozen Classifier v0.2.
- Two independent blind reviewers with 100% agreement.
- **Observed review-trigger recall: 100.0% (13/13).**
- **Observed review-trigger precision: 100.0% (13/13)** for applicable benchmark cases.
- **Unnecessary documentation churn: 0.0%.**
- **UNKNOWN / escalation rate: 15.0% (3/20).**

---

## Upgrading to 0.4.0

0.4.0 removes several ways PyDocSync could print "All symbols synchronized" without having evaluated the code. **Runs that used to pass may now fail — intentionally.**

- **Corrupt or unsupported baseline lockfiles** and **unreadable/unparseable Python files** now fail `check` with exit `2` (previously ignored).
- **Files containing a docstring-only class** (for example an exception class with just a docstring) were silently skipped in their entirety in 0.3.0: none of their symbols were baselined or checked. They are now evaluated, so newly checked symbols may appear as new symbols.
- **Same-named definitions in one file** (redefinitions, `@overload`, property getter/setter) now get one baseline record each. The 0.3.0 baseline held only the last definition, so the first check after upgrading may ask for a one-time `pydocsync accept --symbol <name> --file <path> --reason "..."` per duplicated name.
- **`accept`** refuses an ambiguous name (exit `2`); use `--file`.
- **`init`** protects drifted records (exit `1`); use `--force --reason` to reset deliberately.
- New: `check` coverage line, stale-baseline notice and `--fail-on-stale`, `refresh`, `init --dry-run`, `init --force --reason`, `accept --file`.
- New: `--exclude PATTERN` (all commands) and `<root>/.pydocsync.json` for files that only look like Python; `--no-default-excludes`; `check --require-baseline`; a `pydocsync-check` pre-commit hook. `node_modules` and `site-packages` are now always skipped. Invalid patterns or config files exit `2` instead of being ignored, and `check` reports what your exclusions removed.

---

## Exit Codes

```text
0   Clean / synchronized
1   Synchronization review required, symbol not found (or accept --file on an excluded file),
    init protected drifted records, or stale baseline with check --fail-on-stale
2   A problem prevented a complete evaluation (corrupt baseline, unreadable/unparseable file,
    missing baseline with --require-baseline), ambiguous accept, invalid --exclude pattern or
    .pydocsync.json, or invalid usage. Wins over 1 when both occur.
```

---

## AI Agent Integration & Skills

PyDocSync is designed ground-up for AI-assisted development (Claude Code, Google Antigravity, Cursor, GitHub Copilot, Codex).

To equip your AI coding agent with native PyDocSync workflows in your own project, copy the bundled consumer skill:

- Source: [`.agents/skills/pydocsync/SKILL.md`](.agents/skills/pydocsync/SKILL.md)
- Target: `<your-repo>/.agents/skills/pydocsync/SKILL.md` or `.claude/skills/pydocsync.md`

When installed, the AI agent will automatically:
1. Run `pydocsync check` after editing Python functions or classes.
2. Read the diagnostic output before acting: `PYDOCSYNC001` review obligations, problems (exit `2`), and stale-baseline notices.
3. Update docstrings / contracts when behavior changes, or run `pydocsync accept ... --file <path>` with a clear audit reason if the documentation remains accurate; run `pydocsync refresh` after documented changes.
4. Handle non-Python files with `--exclude` / `.pydocsync.json`, without excluding real source code just to make `check` pass.

---

## License

PyDocSync is open-source software licensed under the [Apache-2.0 License](LICENSE).
