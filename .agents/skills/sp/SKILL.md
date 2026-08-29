---
name: "sp"
description: "Refresh the Spashta CKG (Code Knowledge Graph) and query it for impact / coupling / dead-code analysis. Portable across projects."
argument-hint: "no arg = smart refresh; --force / --stats / --diff; or an impact/coupling question to answer from the graph"
user-invocable: true
disable-model-invocation: false
---

## What Spashta is

Spashta is a **Code Knowledge Graph (CKG)** built over this repository. It indexes Python,
JavaScript, HTML templates, and CSS into nodes (functions, classes, models, routes, templates,
StyleClasses, events…) joined by typed edges (`calls`, `imports`, `renders_template`, `uses_style`,
`resolves_to`, `dispatches_event`/`listens_to`, …). You query it to answer **"what breaks if I
change X?"** and **"what is this coupled to?"** BEFORE editing — impact prediction, not reactive
test-running.

This skill does two jobs: **(1) refresh** the graph, and **(2) query** it to fully utilize the
contributed full-stack + CSS coupling (see the query reference below).

---

## 1 — Refresh the CKG

Run from the **repo root** (the directory containing `spashta_refresh.py`). If `python` fails with
"not found" or import errors, activate the project venv first (`.\.venv\Scripts\Activate.ps1` on
Windows, `source .venv/bin/activate` on POSIX), then retry.

Pick the command from `$ARGUMENTS`:

| Arg | Command | Purpose |
|-----|---------|---------|
| _(none)_ | `python spashta_refresh.py` | Smart refresh — re-enriches only changed files; skips if nothing changed (fast). |
| `--force` | `python spashta_refresh.py --force` | Full re-enrichment regardless of diff. |
| `--stats` | `python spashta_refresh.py --stats` | Node/edge counts only, no rebuild. |
| `--diff` | `python spashta_refresh.py --diff` | Show last diff report only, no rebuild. |

**When to refresh:** at session start (once, before impact work); after adding/removing a Python
file, app, or model field; after renaming a module/class/method; after a template/CSS/JS change you
intend to query. Report the outcome concisely (what changed, counts if shown, any errors).

---

## 2 — Query the CKG (how to fully utilize)

The query CLI lives under the Spashta install, typically
`Spashta-CKG/Spashta_2.1/runtime/query_spashta.py`. All commands run from the repo root.

**Impact / dependency (the core two):**
```
python <…>/runtime/query_spashta.py impact "ClassOrName" --depth 2      # who is affected if I change X
python <…>/runtime/query_spashta.py dependencies "ClassOrName"          # what X depends on
```
- Always run `impact` on the **model class** for a model/service change — field-level changes
  cascade from `Field` nodes outward; checking the service alone misses upstream consumers.
- `impact`/`dependencies` accept a **Route** (`"app:url_name"`), **Event**, or **StyleID** by
  **bare name** (same-name placeholder siblings are unioned) — so one query resolves cross-emitter
  coupling. A **Template** resolves by its FULL node id (a partial's bare filename does not).

**CSS coverage (contributed):**
```
python <…>/runtime/query_spashta.py dead-css                # classes with no template/JS use (CANDIDATES, partitioned)
python <…>/runtime/query_spashta.py class-usage "fp-foo"    # who uses .fp-foo (templates + JS)
python <…>/runtime/query_spashta.py dup-styles              # byte-identical style / @keyframes blocks
```

**What the graph now answers** (all contributed — see `reference/spashta-query-guide.md` for the
full edge catalog, when each applies, and the config that enables it):

- **Frontend → Django route:** `hx-get="{% url 'app:x' %}"` and `path(…, name='x')` join via a
  `Route` node → `impact "app:x"` returns the templates that call a URL + the view that serves it
  (plus views that `reverse()`/`redirect()` there). *"What breaks if I rename this URL?"*
- **View → template:** `render(request, "t.html")` → `renders_template`. *"Which view renders this template?"*
- **Template inheritance/includes:** `{% extends %}` / `{% include %}` → `extends_template` /
  `includes_template`. *"If I change this base/partial, which templates break?"*
- **HTMX event coupling:** `hx-trigger="evt from:body"` (`listens_to`) joined by name to a JS
  `dispatches_event` / an `HX-Trigger` response header. *"Dispatched here, listened where?"*
- **HTMX OOB swaps:** `hx-swap-oob` on `id=X` → `oob_swaps` Template→StyleID. *"Which fragments OOB-refresh `#form-messages`?"*
- **CSS usage:** `class="a b c"` → `uses_style`; `classList.add/toggle('x')` / `querySelector('.x')`
  → `queries_dom`. *"Who uses `.fp-foo`? Is it dead?"*
- **JS calls/events:** cross-file `window.fp.*` calls, callback-by-reference
  (`addEventListener('evt', handler)`), event dispatch↔listen, which DOM class/id a function queries.

**Determinism:** every contributed rule is deterministic-**when-literal** — a templated/computed
value (`hx-get="{% url v %}"`, `_field_form_{type}.html`) is recorded as an **ambiguity**, never a
guess. A `dead-*` list is always a **CANDIDATE** list (a name built entirely in host code can't be
seen) — treat it as high-precision evidence, never a blind delete list.

**Supported stack:** Python + HTML + CSS + JS; frameworks Django, FastAPI, HTMX, vanilla JS (use the
exact spellings in `profile.json`). Python/HTML/CSS need **no third-party dependency**; **JavaScript
needs tree-sitter** (`pip install -r Spashta-CKG/Spashta_2.1/builders/js/requirements.txt`). A
**pure-Python** project just sets `languages: ["python"]` and skips the tree-sitter install.

For the complete edge-type catalog, the "which question → which command/edge" map, **how to
configure `profile.json` (with the relative `project_root`, a full-stack example, and a pure-Python
example), the JS/tree-sitter dependency**, and the new-project setup checklist, **read
[`reference/spashta-query-guide.md`](reference/spashta-query-guide.md)** in this skill folder.

---

## Arguments

```text
$ARGUMENTS
```

If `$ARGUMENTS` is empty or a refresh flag → run the refresh (section 1). If it's an
impact/coupling/dead-code **question** → answer it by querying the graph (section 2), refreshing
first if the graph may be stale.
