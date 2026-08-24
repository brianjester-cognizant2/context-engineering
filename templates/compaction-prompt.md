# Compaction Prompt

> **Tune for recall first, precision second.** Start by preserving too much, verify the agent stays coherent across a compaction boundary, *then* trim. Tuning for brevity first produces a compaction that reads beautifully and has quietly amputated something critical.

**Trigger at ~70% of the *effective* window** (≈60–70% of nominal), not 95%. By 95% you have already spent half the run in the degradation zone.

**Do the free thing first:** clear stale tool results. A file read forty turns ago does not need its contents in context — a one-line reference does. No model call, no risk of losing a decision, and frequently the single largest win available.

---

## The prompt

```
Summarize the agent's work so far, preserving ALL of the following. Omitting any
of these will cause the agent to repeat work or lose the thread.

1. The original goal, verbatim.
2. Decisions made, and the reason for each.
3. Findings — facts discovered, with where they came from.
4. Dead ends — what was tried, that it failed, and WHY.
   Without this the agent will retry them.
5. Open questions and remaining work.
6. Exact identifiers encountered: file paths, IDs, URLs, error strings, version
   numbers. Reproduce these EXACTLY; do not paraphrase.

Omit: verbose tool output, superseded intermediate reasoning, pleasantries.

<trajectory>
{trajectory}
</trajectory>
```

---

## Domain-specific additions

Add whatever your agent establishes early and needs throughout. The generic prompt will not know to keep these, and a summarizer will reasonably treat them as low-value detail.

| Domain | Add |
|---|---|
| Code migration | **Conventions established** — naming, import style, fixture patterns, with a canonical example of each |
| Research | Sources already read and rejected, and why |
| Data analysis | Schema quirks discovered; columns found unreliable |
| Incident response | The timeline built so far, with exact timestamps and trace IDs |
| Customer support | Everything the customer already told you, verbatim |

---

## Verification

- [ ] Run a real trajectory through it and diff pre/post for each of the six items
- [ ] Confirm the agent does not retry a recorded dead end after a compaction boundary
- [ ] Confirm exact identifiers survive unparaphrased
- [ ] **Log compaction boundaries** alongside a quality score — if quality drops as a step function at a boundary, the prompt is dropping something; if it slopes, that is ordinary context rot and needs a different fix
