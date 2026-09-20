# PyDocSync — Deferred Feature Backlog

> Items here are **not being implemented**. Per `AGENTS.md`: when an item moves to active development, run `/speckit-specify <name>` and remove it from this list.
> Source of most items: the v0.3.0 field report (spec `009-silent-false-pass-hardening`) and its implementation findings. Numbers in brackets refer to the reporter's gap table.

## Planned next (spec numbers reserved)

| Spec | Item | Notes |
|---|---|---|
| `010-exclude-option` (target 0.4.1) | `--exclude` option, plus config file / `--path` [11] | Needed by users whose files only *look* like Python (Django/cookiecutter templates): since 0.4.0 an unparseable file exits 2, and the only workaround is moving it under a default-ignored directory. |
| `010-exclude-option` | `check --require-baseline` [11] | Exit 2 when the root has no baseline folder, or has zero lockfiles while public symbols exist (silent pass today). Opt-in flag, default behavior unchanged. |
| `010-exclude-option` | `.pre-commit-hooks.yaml` [11] | Ready-made hook definition; the reporter currently wraps `check` in their own script. |

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
