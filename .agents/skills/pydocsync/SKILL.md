---
name: "pydocsync"
description: "Understand and use PyDocSync for deterministic code-documentation synchronization during AI-assisted Python development."
user-invocable: false
disable-model-invocation: false
---

# PyDocSync

## 1. Purpose

PyDocSync is a lightweight, deterministic code–documentation synchronization engine for Python.

It addresses an acute failure mode in AI-assisted software engineering: **silent documentation drift**. When AI coding agents or developers modify implementation details (e.g. changing parameter defaults, altering raised exceptions, restructuring dictionaries, or reordering call sequences), unit tests often still pass, but docstrings and parameter contracts are frequently left unmaintained or become outdated.

PyDocSync solves this by computing multi-representation AST fingerprints and evaluating code changes against a recorded baseline to determine if a documentation review obligation exists.

---

## 2. Project Information

- **Official GitHub Repository**: [`https://github.com/mpcoder1111/PyDocSync`](https://github.com/mpcoder1111/PyDocSync)
- **Current Version**: `0.4.0 Experimental`
- **Supported Python**: Python `3.10+` (zero runtime dependencies, standard library only)

---

## 3. Why This Project Uses PyDocSync

In AI-assisted pair programming and agentic workflows, LLMs modify code rapidly across multiple files. While linters and test suites check for syntax validity and functional correctness, they do not verify if documentation accurately reflects implementation changes.

```text
AI changes implementation
        ↓
Unit tests may still pass
        ↓
Docstring remains unchanged / outdated
        ↓
PyDocSync detects representation mismatch
        ↓
AI reviews & updates docstring (or explicitly accepts)
```

By adding PyDocSync as an automated gate, this project ensures that all Layer-1 Python contracts, models, and MCP tool handlers help maintain synchronized, reviewable documentation without manual auditing overhead.

---

## 4. How It Works: Multi-Representation Fingerprints & Baselines

PyDocSync extracts and normalizes the Abstract Syntax Tree (AST) of every public function, method, and class across 7 distinct representation planes:

1. **`CODE`**: Canonicalized AST execution flow, expressions, and statements (ephemeral source locations like `lineno` and `col_offset` stripped; AST `ctx` semantics preserved).
2. **`API`**: Function signatures, parameter names, ordering, kind (positional, keyword-only), and default values.
3. **`TYPE`**: Type annotations and return type definitions.
4. **`DOC`**: Extracted docstrings (stripped of leading/trailing whitespace).
5. **`RAISE_TYPE`**: Exception classes raised explicitly in the function body (`ast.Raise`).
6. **`RAISE_DETAIL`**: Literal string messages or formatted arguments passed to exceptions.
7. **`EXAMPLE`**: Runnable code examples or doctest snippets embedded within docstrings.

### The Baseline Concept
Before PyDocSync can detect changes, a **baseline** must exist. The baseline is stored as modular JSON lockfiles under `.project/pydocsync/` (with a top-level `schema_version: 1` envelope). It records the SHA-256 fingerprints of all compliant symbols at a known good state.

> **Important Invariant**: PyDocSync produces a **deterministic review signal** (`PYDOCSYNC001`); it does not mathematically prove that natural-language documentation is correct.

---

## 5. Normal Workflow & Decision Tree

> **Workflow Rule**: After any Python modification, follow the mandatory PyDocSync procedure in `AGENTS.md`; this skill provides the conceptual knowledge needed to make the correct decision.

```text
Baseline exists (.project/pydocsync/)
        ↓
AI / Developer modifies Python code
        ↓
Run scoped unit tests (pytest)
        ↓
Run: pydocsync check
        ↓
 ┌──────┴──────────────────────────────────────┐
PASS (Exit 0)                              FAIL (Exit 1)
                                               ↓
                                      Inspect diagnostic
                                               ↓
                                         PYDOCSYNC001?
                                               ↓
                             ┌─────────────────┴─────────────────┐
                             ↓                                   ↓
                  Implementation changed              Documentation is
                  contract / behavior                 still 100% accurate
                             ↓                                   ↓
                  Update docstring in code            pydocsync accept
                             ↓                        --symbol <name>
                  Run: pydocsync check                --reason "<rationale>"
                             ↓                                   ↓
                           PASS                                PASS
```

---

## 6. CLI Commands & Lifecycle

### `pydocsync init`
```powershell
pydocsync init
```
- **Purpose**: Baselines **new** symbols. Records that `check` currently flags are **protected** (left untouched, listed, exit `1`); records whose documentation was updated (*stale*) are left untouched and reported (use `refresh`). A corrupt lockfile is never overwritten (exit `2`).
- **When to use**: **Only** when onboarding a newly authored module, or when the project has no valid baseline.
- **Safety Invariant**: **NEVER run `init` (or `init --force`) to fix a `pydocsync check` failure.** The right responses are: update the docstring, or `accept` with a reason. `init --force --reason "<why>"` exists only for a deliberate, audited baseline reset; the reason is stored in each overwritten record.
- **Preview**: `pydocsync init --dry-run` shows what would be baselined/protected and writes nothing.

### `pydocsync check`
```powershell
pydocsync check
```
- **Purpose**: Compares current AST fingerprints against `.project/pydocsync/` baselines.
- **Exit Codes & Inspection**:
  - `0`: Nothing requires review. The output states coverage (`checked N files, M symbols`); a stale-baseline notice may follow (see `refresh`).
  - `1`: Synchronization review required (`PYDOCSYNC001`), a symbol was not found (`accept`), `init` protected drifted records, or a stale baseline with `check --fail-on-stale` (`PYDOCSYNC003`). **Always inspect the actual diagnostic output before deciding on remediation.**
  - `2`: A **problem** prevented a complete evaluation (corrupt/unsupported baseline lockfile, unreadable or unparseable Python file such as `SyntaxError line 12`), an ambiguous `accept`, invalid arguments, or a blank audit reason. When drift and problems occur together, exit `2` wins and both are printed. Fix the problems first: they mean part of the project was **not** checked.

### `pydocsync accept`
```powershell
pydocsync accept --symbol <qualname> --reason "<rationale>"
```
- **Purpose**: Explicitly records that a human or AI agent reviewed the changed symbol and verified that the existing documentation remains 100% accurate.
- **Requirements**: Requires a non-empty, descriptive `--reason`. Blank or whitespace reasons are rejected with exit code `2`.
- **Same name in several files**: `accept` refuses to guess (exit `2`) and prints one ready-to-run command per candidate. Add `--file <path>` (relative to the root). The `PYDOCSYNC001` hint already includes `--file`; use it verbatim. A name defined more than once inside one file (redefinition, `@overload`, property getter/setter) is acknowledged as a group and the count is printed.
- **Prohibition**: Never use `accept` blindly to silence a check without verifying docstring accuracy.

### `pydocsync refresh`
```powershell
pydocsync refresh --reason "<why the updated docs match the code>" [--symbol <qualname>] [--file <path>]
```
- **Purpose**: After you change code **and** its docstring together, `check` passes, but the baseline still holds the old docstring, so later code-only changes to that symbol would slip through. `check` lists these as *stale* (`N symbol(s) have updated documentation not yet recorded in the baseline`). `refresh` records exactly those symbols.
- **Safety**: It never touches a record that `check` flags and never baselines new symbols. Requires a non-blank `--reason`. Run it after verifying the docs match the code, then commit the updated baseline.
- **CI**: `pydocsync check --fail-on-stale` exits `1` until stale records are refreshed.
- **Known limit**: until `refresh` has been run, a further code-only change cannot be told apart from the earlier documented one; do not ignore the stale notice.

---

## 7. Programmatic Python API

For embedding in tools, background tasks, or custom MCP verification scripts:

```python
from pydocsync import check, init, accept, refresh, SyncResult, SyncFailure

# Run check programmatically
result: SyncResult = check(root_dir=".")

if not result.is_synchronized:
    print(f"Sync review required for {result.failure_count} symbols:")
    for failure in result.failures:
        print(f"  - {failure.symbol.qualname} in {failure.file_path}")
        print(f"    Reason: {failure.rule_result.reason}")
        print(f"    Changed planes: {', '.join(failure.changed_fingerprints)}")
    for problem in result.problems:  # unparseable files / corrupt baselines: NOT checked
        print(f"  ! {problem.kind.value} {problem.path}:{problem.line} {problem.reason}")
print(f"checked {result.files_checked} files, {result.symbols_checked} symbols; stale: {len(result.stale)}")

# Accept a reviewed symbol programmatically (file= is required if the name exists in several files)
success: bool = accept(
    symbol_qualname="mypackage.module.my_function",
    reason="Refactored internal helper; public contract and exceptions unchanged.",
    root_dir=".",
    file="mypackage/module.py",
)

# Record stale baselines after verifying updated docs match the code
count: int = refresh(root_dir=".", reason="Docs updated together with the code; verified.")
```

`init()` and `accept()` raise typed errors carrying data whenever the CLI would not exit `0` (`InitIncompleteError` with an `InitResult`, `AmbiguousSymbolError` with candidates, `SourceProblemsError`). All derive from `PyDocSyncError` (has `exit_code`; not a `ValueError`). `init_report(...)` returns the details without raising.
```

---

## 8. Complementary Ecosystem Role (What PyDocSync Does NOT Do)

PyDocSync works alongside existing Python quality tools, filling a distinct gap:

| Tool | Focus Area | PyDocSync's Relationship |
|---|---|---|
| **`pytest`** | Functional correctness | PyDocSync verifies doc sync, which tests cannot detect. |
| **`ruff` / `flake8`** | Formatting & static linting | PyDocSync checks semantic AST changes across time/baselines. |
| **`mypy` / `pyright`** | Static type checking | PyDocSync tracks changes in type representations (`TYPE`). |
| **`pydoclint`** | Docstring style compliance | PyDocSync verifies that docstrings stay updated when code changes. |

### Known Limitations
1. **No Semantic NLP Proof**: PyDocSync verifies representation alignment and generates review signals; it cannot evaluate whether human language in a docstring is grammatically or semantically sound.
2. **Static AST Boundary**: Static AST analysis cannot track runtime monkey-patching, dynamic reflection (`getattr`/`setattr`), or inter-procedural heap aliasing across external packages. When encountered, PyDocSync safely routes to `UNKNOWN` with `review_required=True`.

---

## 9. Governance & Immutability Rules

```text
┌─────────────────────────────────────────────────────────────┐
│                 Human Lead / Repository Owner               │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Only humans modify)
                               ▼
            ┌────────────────────────────────────┐
            │             AGENTS.md              │  <-- GOVERNANCE & POLICY
            │     (Authoritative & Protected)    │
            └──────────────────┬─────────────────┘
                               │ (Constrains)
                               ▼
            ┌────────────────────────────────────┐
            │              AI Agent              │
            └──────────┬─────────────────────────┘
                       │ (Consults as domain context)
                       ▼
            ┌────────────────────────────────────┐
            │        PyDocSync SKILL.md          │  <-- KNOWLEDGE & SKILL
            │        (Advisory Context)          │
            └────────────────────────────────────┘
```

- **`AGENTS.md` is Authoritative & Protected**: The AI agent must **never** modify, rewrite, or append to `AGENTS.md` autonomously just because this skill was read.
- **Explicit Permission Required**: If the agent discovers that `AGENTS.md` is missing or its PyDocSync instructions are outdated, it must **report the issue to the human user and receive explicit permission** before making any changes to governance files.
- **Role Separation**: `AGENTS.md` governs agent behavior, project rules, and gates. `SKILL.md` provides domain knowledge, AST concepts, and tool mechanics.

---

## 10. When to Read This Skill

An AI agent should activate or reference this skill when:
- Diagnosing a complex `PYDOCSYNC001` failure or analyzing representation diffs.
- Deciding whether a code modification requires a docstring update vs. an `accept` authorization.
- Writing programmatic scripts or MCP tools that interface with PyDocSync.
- Understanding AST representation planes or baseline envelope versioning.

---

## 11. Reference & Integration

- **Official GitHub Repository**: [`https://github.com/mpcoder1111/PyDocSync`](https://github.com/mpcoder1111/PyDocSync)
- **License**: Apache-2.0
- **Standard CLI Executable**: `.\.venv\Scripts\pydocsync.exe` or `pydocsync`
- **Scope**: Applicable to all Python packages, Layer-1 domain modules, utility classes, and MCP protocol tools.

