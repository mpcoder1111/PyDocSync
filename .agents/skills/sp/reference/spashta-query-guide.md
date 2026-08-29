# Spashta CKG — Full Utilization Guide

How to get the most out of the Spashta Code Knowledge Graph, including every capability contributed
back to the tool. Read this when a task involves **impact prediction**, **coupling questions**, or
**dead-code cleanup**. The `sp` SKILL.md covers the refresh + a quick reference; this file is the
exhaustive catalog.

> **Stack applicability.** The core graph (Python `calls`/`imports`/`defines`, JS calls/events, CSS
> `defines`) works on any project. The **full-stack + CSS coupling** below (routes, templates,
> HTMX, `uses_style`) is **Django + HTMX + CSS**-specific and each rule is **config-gated** — an
> empty config leaves the graph byte-identical, so a non-Django project simply doesn't emit those
> edges. Port freely; the irrelevant rules stay dormant.

---

## The mental model

- **Nodes** = code entities: `Function`, `Class`, `Model`, `Route`, `Template`, `StyleClass`,
  `StyleID`, `Event`, `Keyframes`, `Constant`, `Field`.
- **Edges** = typed relationships between them (below).
- **Placeholders join by name.** Several emitters (Python, HTML, JS, CSS) each create a node for the
  same logical thing (a route, an event, a CSS class) and Spashta **joins them by name** — it does
  not merge them into one node. `impact`/`dependencies` **union same-name siblings** for
  `Route` / `Event` / `StyleID`, so one CLI query resolves cross-emitter coupling.
- **Deterministic-when-literal.** A rule fires only when the value is a literal
  (`hx-get="{% url 'app:x' %}"`, `render(…, "t.html")`, `class="a b"`). A computed/templated value
  (`{% url v %}`, `_field_form_{type}.html`) is recorded as an **ambiguity**, never guessed.

---

## The two commands you use most

```
python <spashta>/runtime/query_spashta.py impact "Name" --depth 2
python <spashta>/runtime/query_spashta.py dependencies "Name"
```

- `impact "X"` → **what is affected if I change X** (inbound: callers, renderers, references).
- `dependencies "X"` → **what X depends on** (outbound).
- **Rule:** for a model/service change, run `impact` on the **model class**, not just the service —
  field changes cascade from `Field` nodes and a service-only query misses upstream consumers.
- **Accepted keys:** a bare name; a **Route** as `"app:url_name"`; an **Event** or **StyleID** by
  bare name (siblings unioned). A **Template** resolves only by its **full node id** (its
  `/templates/`-relative logical name), not a partial's bare filename.

---

## Edge catalog — "which question → which edge/command"

### Python structure (core, always on)
| Question | Edge |
|---|---|
| Who calls this function? | `calls` |
| What does this module import? | `imports` |
| Class members / definitions | `contains_member` / `defines` |

### Frontend → Django routes
| Question | How |
|---|---|
| What breaks if I rename URL `app:x`? | `impact "app:x"` — unions the `Route('app:x')` siblings |
| Which templates call this URL? | `hx-get`/`href="{% url 'app:x' %}"` → resolved to the Route (`resolves_to` carries a `confidence`: structural = import-proven, heuristic = labelled unique-name match) |
| Which view serves this URL? | `dependencies "app:x"` → the view via `resolves_to` (`path(…, view, name='x')`) |
| Which views redirect here? | `reverse()`/`redirect()`/`reverse_lazy('app:x')` → `calls_api` to the Route |

### View ↔ template
| Question | Edge |
|---|---|
| Which view renders this template? | `render(request, "t.html", …)` → `renders_template` |
| If I change this base/partial, which templates break? | `{% extends %}` → `extends_template`; `{% include %}` → `includes_template` |
| URLconf include tree | `include('app.urls')` → `includes_urlconf` (File→File) |

### HTMX behavior coupling
| Question | Edge |
|---|---|
| This event is dispatched here — who listens? | JS `dispatches_event` / `HX-Trigger` header ↔ `hx-trigger="evt from:…"` `listens_to`, joined by name on one `Event` node |
| Inline `HX-Trigger` (no helper) | `response['HX-Trigger'] = 'ev'` / `json.dumps({'ev':…})` → `dispatches_event` (generic `header_event_dispatch`) |
| Which fragments OOB-refresh `#thing`? | `hx-swap-oob` on `id=X` → `oob_swaps` Template→StyleID (bare id, unifies with CSS StyleID + JS `getElementById`) |

### CSS coverage
| Question | Command / edge |
|---|---|
| Who uses `.fp-foo`? | `class-usage "fp-foo"` — `uses_style` (markup) + `queries_dom` (JS `classList`/`querySelector`) |
| Is `.fp-foo` dead? | `dead-css` — **partitioned** into `dead_classes` / `dynamically_referenced` (name in a `dynamic_class_unresolved` ambiguity, or a BEM `x--{{ … }}` modifier base) / `framework` (`htmx-*` runtime-injected) |
| Duplicate style / animation blocks | `dup-styles` — normalized `body_hash` over rules + `@keyframes` |
| Animation reuse | `@keyframes` → `Keyframes` node + `uses_animation` |

### JS internals
| Question | Edge |
|---|---|
| Who calls this JS function (incl. cross-file `window.fp.*`)? | `calls` |
| Callback passed by reference (`addEventListener('evt', fn)`) | resolved via `calls` (same registry+ambiguity as a direct call) |
| Which DOM class/id does this function touch? | `queries_dom` → `StyleClass` / `StyleID` (joined to CSS by name) |

### Django forms / signals (generic, fires only if present)
| Question | Edge |
|---|---|
| Which model does this ModelForm use? | `ModelForm` + `Meta.model` → `uses_model` |
| What does `@receiver(SIG)` listen to? | `@receiver(SIG)` → `listens_to` |

---

## Dead-code cleanup — the safe SOP

`dead-css` (and any `dead-*` query) reports **CANDIDATES**, not proof. A class built entirely in host
code (string-concatenated, injected by a framework) cannot be seen. **Never bulk-delete off the raw
list.** The four-fold accuracy check (each shipped as a partition in the output):

1. **Literals interleaved with dynamic syntax** are real uses — the tokenizer strips `{% %}`/`{{ }}`
   and keeps a literal class between tags (`class="a {% if x %}b{% endif %}"` → both `a` and `b`).
2. **A naming ambiguity is soft evidence of use** — a class named in a `dynamic_class_unresolved`
   ambiguity is `dynamically_referenced`, not dead.
3. **Framework-injected symbols** (`htmx-*`) are allowlisted, not dead.
4. **A variable-filled BEM modifier** (`x--{{ status }}`) means `x--active` etc. are
   `dynamically_referenced` via their base.

Then: brace-matched removal (keep suffixed siblings + grouped/live selectors) → re-run `dead-css`,
the count must drop by **exactly N** → run the project's frontend guards + a **browser smoke**.

---

## Contributed capabilities (provenance)

All merged to the Spashta repo `master`; each is additive, config-gated, deterministic-when-literal,
with a fixture + a `verify_*` proof; structural edges unchanged on rebuild. Named specs in the
Spashta install under `spec/`:

- `htmx-event-coupling.md` — `hx-trigger from:` → `listens_to`, joined to JS `dispatches_event`.
- `frontend-route-coupling.md` — `path(…, name='x')` → `Route('app:x')` + `resolves_to` (tiered:
  structural import-proven + heuristic unique-name; every edge carries `confidence`).
- `django-htmx-coupling.md` — `render()`→template, `reverse/redirect`→route, `HX-Trigger` helper→event.
- `fullstack-coupling-roadmap.md` (P1–P5) — template inheritance/includes, URLconf include tree,
  generic inline `HX-Trigger`, Django forms/signals (`uses_model`, `@receiver`), HTMX OOB swaps.
- `css-coverage-roadmap.md` (P1–P3) — `uses_style`, `@keyframes` modeling, `dead-css`/`class-usage`/
  `dup-styles` + JS `classList` → `queries_dom`.
- `dead-code-accuracy.md` (P1–P4) — the four-fold `dead-css` accuracy partitioning above.
- `js-callback-refs.md` — `addEventListener('evt', handler)` resolves the by-reference handler.
- Builder-consistency fix — all three builders (Python/HTML/JS) honor the project scan exclusions
  (`profile.json` `excluded.directories` + `builder_rules.json` `scan_policy.exclude_dirs`). Exclude
  vendored/synced/doc-snapshot dirs, or duplicate names defeat the name-based resolvers.

---

## What Spashta supports (the stack it's designed for)

Spashta is built for a **Python web-app stack**. Use the **exact spellings** below in `profile.json`
(`_meta.supported_*`) — a typo silently disables a language/framework:

- **Languages:** `python`, `html`, `css`, `js`
- **Frameworks:** `django`, `fastapi`, `htmx`, `vanilla` (vanilla = plain JS)

Python/HTML/CSS parse with **no third-party dependency** (stdlib `ast` + built-in parsers).
**JavaScript is the exception** — it needs **tree-sitter** (see below). A project can enable any
subset: pure-Python, Python+HTML+CSS, or the full Django+HTMX+vanilla-JS stack.

### JavaScript needs tree-sitter (the dependency you forgot)

Indexing `js` requires two pip packages (a C library with Python bindings — **no Node.js runtime**,
error-tolerant, MIT):

```
tree-sitter>=0.23,<1.0
tree-sitter-javascript>=0.23
```

They live in `Spashta-CKG/Spashta_2.1/builders/js/requirements.txt`. Install into the **Spashta
venv** (the one that runs `spashta_refresh.py`):

```
pip install -r Spashta-CKG/Spashta_2.1/builders/js/requirements.txt
```

If `js` is in `profile.json.languages` but tree-sitter isn't installed, the JS builder errors.
**A pure-Python project doesn't need this at all** — omit `js` from `languages` and skip the install.

---

## Configuring `profile.json`

The activation file is `Spashta-CKG/Spashta_2.1/project/profile.json`. It declares the stack and the
scan scope. Fields:

| Field | Meaning |
|---|---|
| `project_root` | **The path Spashta scans, RELATIVE to the `Spashta-CKG` folder.** `".."` = the parent dir (Spashta lives *inside* the repo, the normal layout). If Spashta-CKG is **not** inside the project, use an **absolute path** to the repo root instead. |
| `project_type` | `web_app`, `library`, `cli`, … (informational). |
| `languages` | The active languages to index (subset of the supported list). |
| `frameworks` | The active frameworks (subset of supported). |
| `excluded.directories` | Project dirs to skip — **vendored, generated, and doc-snapshot copies** (added to the built-in `node_modules`/`.git`/`__pycache__` exclusions). Critical: a duplicate/synced copy of code defeats the name-based joins (routes/events/CSS), creating false "2 definitions" ambiguities. |
| `excluded.frameworks` / `excluded.languages` | Supported items you deliberately leave off. |

### Example A — full Django + HTMX + vanilla-JS stack (this project's live config)

```json
{
  "project_root": "..",
  "project_type": "web_app",
  "languages": ["python", "html", "css", "js"],
  "frameworks": ["django", "htmx", "vanilla"],
  "excluded": {
    "frameworks": ["fastapi"],
    "languages": [],
    "directories": ["Spashta-CKG", "misc", "reference"]
  }
}
```

Requires the tree-sitter install (because `js` is active). Always exclude the `Spashta-CKG` folder
itself, plus any vendored/synced/doc-snapshot dirs.

### Example B — pure-Python project (no HTML/CSS/JS, no tree-sitter)

```json
{
  "project_root": "..",
  "project_type": "library",
  "languages": ["python"],
  "frameworks": [],
  "excluded": {
    "frameworks": ["django", "fastapi", "htmx", "vanilla"],
    "languages": ["html", "css", "js"],
    "directories": ["Spashta-CKG", "tests/fixtures", "build", "dist"]
  }
}
```

You get the **core Python graph** — `impact` / `dependencies` over `calls` / `imports` /
`defines` / `contains_member` (functions, classes, module-level constants). **No pip deps beyond
Spashta's own** (Python parses with stdlib `ast`). The full-stack + CSS coupling rules stay dormant
(nothing to emit), so the graph is just the Python structure — exactly what a library/CLI wants for
"what breaks if I change this class/function?".

If the project uses a web framework but no templates/JS (e.g. a FastAPI JSON API), set
`languages: ["python"]`, `frameworks: ["fastapi"]` — still no tree-sitter.

---

## Porting to a new project — setup checklist

1. **Copy the Spashta install** (`Spashta-CKG/…`) and the `spashta_refresh.py` wrapper into the new
   repo root (the normal layout → `project_root: ".."`). Or keep a shared install elsewhere and set
   `project_root` to the repo's **absolute path**. Copy this `sp` skill folder into the new
   project's `.claude/skills/`.
2. **Edit `project/profile.json`** — pick `languages` + `frameworks` for the target stack (Example A
   or B above), fix `project_root`, and list vendored/generated/synced dirs under
   `excluded.directories`. Use exact spellings.
3. **If `js` is active, install tree-sitter** into the Spashta venv
   (`pip install -r Spashta-CKG/Spashta_2.1/builders/js/requirements.txt`). Pure-Python → skip.
4. **Enable the coupling rules** you want in `builders/builder_rules.json` (route registrations, call
   couplings, template inheritance, CSS coverage…). Each is config-gated: an empty section stays
   dormant — safe for a non-Django/non-HTMX/pure-Python stack.
5. **First build:** `python spashta_refresh.py --force`, then `--stats` to confirm node/edge counts.
6. **Verify a query round-trips:** `impact "SomeClass"` (any stack) and, for Django,
   `dependencies "app:some_url"`.
7. **Optional guard:** the reference project ships a fast, Spashta-free frontend contract guard
   (`test_frontend_contracts.py`) + a richer over-the-graph audit (`scripts/frontend_audit.py`,
   HTMX-aware). These are **project-specific** consumers, not part of Spashta core — re-derive per
   project if wanted.

---

## Known scope limits

- Cross-language nodes are **joined by name, not merged** — a name collision across a
  vendored/synced copy creates a false "2 definitions" ambiguity (fix: exclude the copy).
- No full JS semantics — no `fetch`→route wiring beyond the modeled HTMX attrs, no React/Vue/TS-type
  edges. Treat JS coupling as a foundation + references, not a complete model.
- **Cascade / computed CSS is out of scope by design** (runtime; unneeded for grounding).
- A `dead-*` result is a **candidate** — aim for high precision, not omniscience.
