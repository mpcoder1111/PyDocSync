# PyDocSync — Deferred Feature Backlog

> Items here are **not being implemented**. Per `AGENTS.md`: when an item moves to active development, run `/speckit-specify <name>` and remove it from this list.
> Source of most items: the v0.3.0 field report (spec `009-silent-false-pass-hardening`) and its implementation findings. Numbers in brackets refer to the reporter's gap table.

## Delivered

- Spec `010-exclude-and-require-baseline` (in 0.4.0): `--exclude`, `.pydocsync.json`, `--no-default-excludes`, `check --require-baseline`, `.pre-commit-hooks.yaml`, `node_modules`/`site-packages` default ignores (field-report items 6, 7 and 11).

## Backlog from spec 010

- **`--path`** (scan only listed files/dirs): rejected for now because `check` takes milliseconds on a whole project and `accept --file` / `refresh --file` already scope writes; revisit if very large monorepos need it.
- **`--include` / negation patterns (`!x`)**: rejected because order-dependent rules are the classic gitignore trap; `--no-default-excludes` covers the real need (code in `pkg/build/`).
- **TOML / `pyproject.toml` config, `--config PATH`, nested per-directory configs, environment-variable config**: JSON at `<root>/.pydocsync.json` only, because Python 3.10 has no stdlib TOML reader.
- **Executing the pre-commit hook under the real `pre-commit` tool** in CI (only its manifest and entry command are tested).

## Considered and deferred

### MCP server alongside the CLI (owner decision 2026-09-20: not now)

Raised as "implement MCP alongside the CLI, exposing as much of the CLI as possible", using Spashta-CKG's MCP server as inspiration. Deferred after grounding, because PyDocSync runs once per batch of edits (pre-commit / CI), not as a frequent interactive query like a code graph, and agents with a shell already use the CLI while programmatic callers use the Python API.

Grounded findings, so the research is not repeated:
- Spashta-CKG's `spashta_ckg/mcp_server.py` uses the official `mcp` SDK (a runtime dependency): FastMCP-style decorators, stdio transport, 10 tools prefixed `spashta_*`, a free `project_dir` parameter, dual delivery (JSON text `content` plus `structuredContent`), a `--help` catalog and a console script `spashta_ckg_mcp`.
- PyDocSync's constitution (Principle I) forbids runtime dependencies, and `mcp` is not installed here. Options: a hand-written stdlib JSON-RPC stdio server, or an optional `pydocsync[mcp]` extra (needs a constitution amendment).
- The current SDK (`mcp 2.1.1`) speaks two protocol eras: the classic `initialize` handshake (2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25) and a stateless per-request envelope (2026-07-28, discovered via `server/discover`). A modern client falls back to `initialize` on any JSON-RPC error from `server/discover`, so a handshake-only stdlib server would still work with new clients. A hand-written server must also keep stdout reserved for the protocol (the SDK guards the stdio file descriptors against stray prints).
- The `run_*` functions introduced by spec 009 already return structured data, so an MCP layer would be a thin adapter if it is ever wanted.
- Design sketch that was proposed (not decided): tools `pydocsync_check/init/accept/refresh` with read-only/destructive hints and a `--read-only` mode, a pinned project root with containment for `project_dir`/`file`, an optional workflow prompt and baseline resources.

Revisit if users ask for it, or if agents without shell access need PyDocSync.

### Structured CLI output (`--json`)

Cheaper alternative that covers the "agents/wrappers want data" need without a protocol: a `--json` flag on `check`, `init`, `accept`, `refresh` emitting the same structures as the Python results (`SyncResult`, `InitResult`, `Problem`, `StaleRecord`) and the exit code. Not yet specified; would be its own small spec if wanted.

## Field-report items not yet scheduled

| # | Item | Notes |
|---|---|---|
| 5 | `init` says "compliant symbols" but counts undocumented ones | Wording only; existing tests assert the current sentence, so change both together. |
| 6 | Directory names (`build`, `dist`, `tests`, `fixtures`) are skipped **wherever** they appear (e.g. `pkg/build/`) | Consider anchoring exclusions to the root, or per-path rules; belongs with the config-file work. |
| 7 | `node_modules` and `site-packages` are not in the default ignore list | Trivial addition; document in the same change as [6]. |
| 8 | Reported paths are relative to `--root` only (`app\m.py`, not the package) | Add an optional absolute or cwd-relative rendering; affects hints (`--file`, `--root`). |
| 9 | `python -m pydocsync.cli` prints a `RuntimeWarning` | `python -m pydocsync` is unaffected; fix by not re-importing `cli` from `__init__` on that path. |

## Findings from spec 009 implementation

- **Default-strict stale baselines** (candidate for 0.5.0): make `check` fail (exit 1) when documentation was updated but the baseline was not refreshed, with an opt-out (`--allow-stale`). Deferred because it changes the prescribed "update docstring → check → pass" workflow and the evaluation results of specs 003/004.
- **Python `accept()` does not validate a blank reason** (only the CLI does). Should raise `InvalidArgumentError`, like `refresh()` / `init(force=True)` do.
- **Retire the lenient `BaselineManager.load_module_baseline`** (kept only because a shipped test pins it); remove in a future major version.
- **Module-qualified baseline keys** (`pkg.mod.Command.handle`): cleaner identity than `name#N` positional keys, but a baseline schema change (T4). Future major version.
- **Baselines of deleted files/symbols are never reported** (a different meaning of "stale": the source is gone). Needs its own spec (report vs. prune).
- **Atomic lockfile writes** (write to a temp file, then replace): would remove a way lockfiles get truncated in the first place.
- **AGENTS.md has no PyDocSync procedure section**, although the consumer skill refers to one. Needs an owner-authored policy text.
