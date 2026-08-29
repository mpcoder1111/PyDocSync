---
name: "vsp"
description: "Answer very short, as explained POINTS — a tight bulleted list, each point a label + a one-line explanation. No prose walls, no headers."
argument-hint: "The question or topic to answer briefly in points"
user-invocable: true
disable-model-invocation: false
---

## Instruction

Answer the user's question (from `$ARGUMENTS`) as a **very short bulleted list of explained points**.

Rules:
- **Points, not paragraphs.** Aim for **3–6 bullets**, each **1–2 sentences**: a bolded label/claim, then a brief "why/how" explanation. Fewer bullets is fine; more than ~6 means you're over-answering.
- One optional lead-in line ONLY if the points need a sentence of context first — otherwise start straight at the bullets.
- No headers, no preamble ("Great question", "Sure"), no trailing summary.
- Nested sub-bullets only if a point genuinely needs one detail; keep depth to one level.
- Include the "why" when it's non-obvious; drop it when the point is self-evident.
- Code/paths in `backticks`; a one-line code snippet is fine inside a bullet if it's the clearest answer.
- If the answer truly needs more, give the most important points and end with "more detail available if needed".

## User Question

```text
$ARGUMENTS
```

Answer now, following the rules above.
