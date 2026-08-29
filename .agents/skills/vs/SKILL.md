---
name: "vs"
description: "Answer in very short form — 1 to 2 paragraphs max, no headers, no bullet lists unless unavoidable."
argument-hint: "The question or topic to answer briefly"
user-invocable: true
disable-model-invocation: false
---

## Instruction

Answer the user's question (from `$ARGUMENTS`) in **1–2 paragraphs maximum**.

Rules:
- No headers
- No bullet lists unless a list is literally the only sensible format
- No preamble ("Great question", "Sure", etc.)
- No trailing summary
- If the answer genuinely needs more than 2 paragraphs to be correct, write the 2 most important ones and say "more detail available if needed"

## User Question

```text
$ARGUMENTS
```

Answer now, following the rules above.
