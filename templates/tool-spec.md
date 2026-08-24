# Tool Specification: `<tool_name>`

> A tool description is **prompt surface** — it is in the model's context on every turn, competing for attention with everything else. Rewriting one is a behavior change: version it and re-run your evals.

---

## Schema

```json
{
  "name": "<exact function name>",
  "description": "<what it does>. Returns <what it returns>. Use this when <X>; use `<other_tool>` when <Y>.",
  "input_schema": {
    "type": "object",
    "properties": {
      "<param>": {
        "type": "string",
        "description": "<what it is AND what format>, e.g. '<concrete example>'.",
        "enum": ["<constrain where possible>"]
      }
    },
    "required": ["<mandatory params>"]
  }
}
```

---

## Checklist

- [ ] **Description states what it RETURNS**, not just what it does
- [ ] **"Use this when… use X when…"** clause present — the clause that prevents the most errors
- [ ] Every parameter description gives a **format example**
- [ ] `enum` used wherever the value set is closed
- [ ] `required` is accurate
- [ ] **No overlapping tool.** If a human engineer would hesitate between this and another, merge or delete one
- [ ] Not secretly a **field of another object** (`get_price` is usually part of `get_product`)
- [ ] **Self-contained** — does not require another tool to have been called first in a specific order
- [ ] Reads separated from writes
- [ ] Irreversible actions marked destructive and gated in the harness, not discouraged in the prompt

---

## Error contract

Design error paths as carefully as success paths — the agent reads them at exactly the moment it most needs guidance.

| Condition | Returned to the agent |
|---|---|
| Not found | `"No <thing> matching <input>."` + **hint** naming the fallback tool + **similar candidates** |
| Invalid argument | The problem, the **expected format**, and a concrete example |
| Both missing and unknown args | **Report both** — a typo like `e_mail` is simultaneously each; reporting one sends the agent chasing half the problem |
| Upstream failure | What failed, whether retrying helps, what to try instead |
| Permission denied | That it was denied, and what to propose instead |

- [ ] **No error path raises into the loop.** An exception kills the run; a returned error is an observation the agent recovers from

---

## Result design

Tool results accumulate in the context window on every subsequent turn.

- [ ] **Typical result size:** ______ tokens
- [ ] **Worst-case result size:** ______ tokens
- [ ] Large results **summarized + offloaded** to a reference the agent can grep or range-read
- [ ] Broad match sets return **facets**, turning "too many results" into a next action
- [ ] `limit` / `detail` parameter so the agent can ask for more
- [ ] Truncation is **loud** — silent truncation reads as "this is the whole result"

---

## Cost

- **Schema tokens:** ______ × every turn
- **Justification:** what wasted turn does this description prevent, and how often?
