# **Changelog**

## **2026 Edition**

The field reorganized between 2023 and 2026. This edition follows that reorganization rather than appending to the old structure.

### **The Structural Change**

**Retired: Context Window Architecture (CWA).** The previous edition closed with an 11-layer model prescribing the ideal ordering of a single prompt. That answered a 2023-shaped question. Agents don't have one prompt — they assemble context dozens of times per task, across sub-agents with separate windows, over sessions that outlive any single window.

**Added: Module 8, Agentic Engineering** — a full module in its place, covering the harness, loop engineering, structuring AI teams, and a six-plane **Agentic Architecture** that organizes every technique in the course.

CWA's surviving insight — that context assembly is a deliberate design act rather than string concatenation — is now the Context plane of that model, updated for prompt caching and agent loops.

### **New Lessons**

| Lesson | Why |
| :--- | :--- |
| **1.4 The Four Disciplines** | The course now has a spine — prompt → context → harness → loop — and learners need the map early |
| **3.5 Agentic Retrieval** | Grep-based agentic search displaced vector RAG for code in 2025–2026. Choosing between them is now a core skill |
| **4.4 Long-Horizon Context** | Compaction, structured note-taking, sub-agent isolation, and just-in-time retrieval — the techniques that keep hours-long agents coherent |
| **5.4 MCP and Agent Skills** | MCP became ubiquitous and went stateless; Agent Skills became an open standard with progressive disclosure |
| **8.1 The Harness** | `Agent = Model + Harness`. Most production failures are harness failures |
| **8.2 Loop Engineering** | The shift from prompting agents to building systems that prompt agents |
| **8.3 Structuring AI Teams** | Orchestration patterns, handoff contracts, and the human roles that appeared alongside them |
| **8.4 Agentic Architecture** | The unifying capstone that replaces CWA |

### **Substantially Revised**

*   **1.1** — Explicit prompt-engineering vs. context-engineering distinction; expanded context components (memory, task state, tool results).
*   **1.2** — Agent-scale token economics, prompt caching (including the stable-to-volatile ordering rule), and model routing. The napkin-math exercise now costs an agent run with and without caching.
*   **1.3** — Added **Altitude** as a fifth design principle; new exercise on fixing an over-specified prompt.
*   **2.1** — The system prompt as a trust boundary; what does *not* belong in a prompt; positive over negative instructions.
*   **2.2** — When examples hurt: reasoning models, output capping, and where a schema is strictly better.
*   **2.3** — Native reasoning vs. explicit CoT; the ceiling on self-critique; schema-enforced structured output replacing "JSON mode"; decomposition for localizability.
*   **3.1** — RAG positioned as one grounding strategy among several.
*   **3.2** — Added **contextual retrieval** and structure-aware chunking.
*   **3.3** — Hybrid search as the recommended default, with Reciprocal Rank Fusion.
*   **4.1** — The context-rot research (18 models), the attention-budget framing, effective context at 60–70% of nominal, edge-loading, and code-enforced token budgets.
*   **4.3** — Replaced the Focused Transformer section, which was both dated and inaccurately described, with contextual retrieval, query transformation (multi-query, HyDE), and late-interaction retrievers — plus an explicit priority order for where to spend effort.
*   **5.1** — Agent vs. workflow ("if you can draw the flowchart, build the flowchart"); ReAct's weak stopping condition named.
*   **5.2** — Tool-set bloat and its diagnostic; actionable error design; token-efficient tool results; tool descriptions as prompt surface.
*   **5.3** — Current framework landscape; plan-act-replan; a minimal agent loop written out; how to adopt a framework without marrying it.
*   **6.1** — Trajectory evaluation across six dimensions; LLM-judge calibration and bias; eval set sizing.
*   **6.2** — OpenTelemetry GenAI conventions; the four agent failure patterns visible in a trace; the divergence-point debugging procedure.
*   **6.3** — Rewritten around **indirect** prompt injection and the **lethal trifecta**, separating defenses that reduce likelihood from those that contain damage. Red-team evals in CI.
*   **7.1** — Extended to computer-using agents and the security cost of visual context.
*   **7.2** — Rewritten: the reliability race, the four-standard interoperability stack, agentic search, meta-agents, and portable observability.
*   **7.3** — Extended from generation ethics to **autonomy ethics**: named accountability, meaningful versus rubber-stamped oversight, error at scale, and displacement.

### **Corrections**

*   **Focused Transformer (FoT)** was described as a contrastive method for improving embeddings. That mischaracterized the technique, and it was never widely adopted in production RAG. Removed.
*   **"Needle in a haystack"** was presented as the state of the art in long-context evaluation. It is now understood as a weak test — passing it does not imply reliable reasoning over long context. Reframed, with the real degradation research in its place.
*   **JSON mode** was presented as guaranteeing valid JSON. Superseded by schema-enforced structured output, which is a categorical improvement rather than an incremental one.
*   **Autogen** was listed as a current multi-agent framework. It was absorbed into the Microsoft Agent Framework.
*   **Delimiters as an injection defense** were presented without the caveat that prompt-level defenses fail against adaptive attackers. Corrected in 1.3 and 6.3.

### **New Supporting Files**

*   **REFERENCES.md** — primary sources, with a note on which figures to trust and which to treat as directional.
*   **CHANGELOG.md** — this file.
*   **GLOSSARY.md** — substantially expanded; superseded terms retained and marked *(historical)* so older material stays readable.

---

## **2026 Edition, revision 2 — Making the Course Runnable**

The taught material was sound but unverifiable: 40 illustrative code snippets and nothing you could execute. A course about **engineering** should let you run the thing it describes and watch it fail when you break it.

### **`code/` — a dependency-free reference harness**

Standard library only, Python 3.10+, no API key. `MockModel` makes the whole package deterministic and offline — not for convenience, but because *a harness you can only observe by spending money on a live API is a harness you cannot test*.

| Module | Implements |
| :--- | :--- |
| `context.py` | Budgeted, cache-aware assembly; cross-call prefix audit; edge-loading |
| `tools.py` | Schemas as prompt surface, actionable errors, result sizing |
| `loop.py` | The agent loop and its five guardrails |
| `compaction.py` | Compaction policy and prompt; stale tool-result clearing |
| `workspace.py` | File-backed structured note-taking |
| `verify.py` | Verification tiers; refusal to build a self-report loop |
| `trace.py` | OTel-shaped spans, cost accounting, thrashing detection |
| `evals.py` | Trajectory scoring, eval-set sizing, judge calibration |

**57 tests.** Each guardrail claim in Module 8 has a test that fails if the guardrail is removed — the test suite is the course's argument in falsifiable form.

**Six runnable examples**, including `03_agent_loop.py` (the same model under two harnesses: victory declaration bias, then verified success) and `06_security.py` (one injection, five capability configurations).

### **Three things the code found wrong in the prose**

Writing the implementation falsified three claims the lessons implied:

*   **A cache-order guard that could never fire.** The lessons frame the cache bug as "don't put volatile content above stable content" — which sorting trivially fixes, so the guard was dead code. The bug that *actually* happens is a volatile value **mislabelled** as stable, which ordering cannot detect. `ContextAssembler` now audits the prefix across calls and notices it is no longer byte-identical. Module 4's guidance is sharper as a result.
*   **Thrashing detection keyed on the wrong thing.** Keying on tool *arguments* misses the real case — three rephrasings of a query are three genuinely different calls returning the same result. Keying on the tool *name* over-fires on an agent legitimately reading ten files. Keying on **tool-plus-result** is correct. Corrected in Module 6, Lesson 2.
*   **Half-reported argument errors.** A typo like `e_mail` for `email` is simultaneously a missing argument and an unknown one; reporting only the first makes the agent add `email` while still sending `e_mail`. Two turns wasted on one typo. `ToolRegistry` reports both, and Module 5, Lesson 2 now says so.

### **Practitioner references**

*   **CHEATSHEET.md** — every decision the course asks you to make, on one page, plus the numbers worth remembering.
*   **ANTI_PATTERNS.md** — a diagnostic reference organized by **symptom** rather than topic, because when something is wrong you know what you're seeing, not what chapter it's in. Fourteen failure modes, each with the fix that works and the fix people reach for first that doesn't.
*   **INDEX.md** — concept → lesson → implementation.
*   **templates/** — architecture spec, eval set, red-team cases, tool spec, compaction prompt, and AGENTS.md skeleton.

### **Course logistics**

*   Every module README now states **learning outcomes**, a **time estimate** (28–35 hours total), and a **Check yourself** set with section references.
*   README gained **prerequisites** and three **learning paths** — building, debugging, or learning the field properly.

### **Accessibility**

*   All 19 Mermaid diagrams carry `accTitle` and `accDescr`, so screen readers get a real description rather than silence. Validated against the Mermaid parser.
*   Fixed a pre-existing diagram in Module 5, Lesson 1 that failed to parse (unquoted `"Cupertino, CA"` in a node label), and quoted several node labels containing parentheses.
