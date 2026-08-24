# **Cheat Sheet**

Every decision this course asks you to make, on one page. Each entry links to where it's derived.

---

## **Numbers worth remembering**

| Number | What it means |
| :--- | :--- |
| **60–70%** | Effective context as a fraction of nominal. Plan against this, not the marketing figure |
| **~30%** | Mid-context recall loss at scale, across all 18 frontier models tested |
| **~70%** | Compact here — of the *effective* window, not the nominal one |
| **~90% / 1.25×** | Prompt cache: read discount / write premium. Prefix valid only to the first changed byte |
| **~60%** | Cache hit rate below which caching may cost more than not caching |
| **~100** | Minimum eval cases before aggregate metrics mean anything (20 cases → ±22% margin) |
| **300–500+** | Eval cases for metrics you can slice and act on |
| **~0.6** | Cohen's kappa floor for a usable judge. Below it, fix the *rubric* |
| **3–7** | Agents in a team. Below: you didn't need a team. Above: coordination eats specialization |
| **~N×, ~(N+1)×** | Cost of fan-out/pipeline, and of supervisor |
| **1.5k / 50k** | What a sub-agent returns vs. what it spends. The compression ratio nothing else matches |

---

## **Which discipline is my problem?**

| Symptom | Discipline | Fix shape |
| :--- | :--- | :--- |
| Wrong format or tone | **Prompt** | Clearer instruction, one canonical example |
| Confidently wrong facts | **Context** | Grounding, retrieval quality, verified citations |
| Degrades in long sessions | **Context** | Compaction, restate constraints at the end |
| Wrong tool chosen | **Context** | Prune overlapping tools; sharpen descriptions |
| Claims success falsely | **Harness** | External verification gates termination |
| Costs 10× the estimate | **Context + Harness** | Cache order, model routing, budget caps |
| Exceeded its permissions | **Capability** | Scope permissions, sandbox, egress allow-list |
| Fine by hand, useless unattended | **Loop** | Trigger, verifiable goal, escalation |

> **If you're adding a sentence to a prompt to prevent a failure that has happened twice — you need structure, not words.**

---

## **Retrieval strategy**

```
Structured data?            -> Query it (SQL / API). Not retrieval.
Exact identifiers + links?  -> Agentic search (glob, grep, read, follow)
Fuzzy prose, large corpus?  -> Hybrid RAG (vector + BM25 + rerank)
Fuzzy prose, < ~50 docs?    -> Just include it. Retrieval is overhead.
Query has an exact token?   -> Keyword first, semantic as fallback
```

**Priority order for improving retrieval** (cheapest and highest-leverage first):

1. **Hybrid search** — never worse than pure vector; removes exact-identifier failures
2. **Contextual retrieval** — one-time index cost, zero per-query cost
3. **Re-ranking** — big gain, no re-indexing
4. **Query transformation** — multi-query, HyDE
5. **A new embedding model** — last; it means re-indexing everything

**Failure modes differ in kind:** vector RAG fails *silently and plausibly*; agentic search fails *loudly*. Where a confident wrong answer beats no answer, that asymmetry matters more than any benchmark.

*(Module 3 Lessons 3, 5 · Module 4 Lesson 3)*

---

## **Memory strategy**

| Strategy | Use when | Weakness |
| :--- | :--- | :--- |
| **Sliding window** | Only recent context matters | Forgets abruptly, including the goal |
| **Summarization** | Long conversation, early content stays relevant | Misremembers — confident, not blank |
| **Hybrid** | Almost always in production | More moving parts |
| **Compaction** | Agents, long trajectories | Lossy by construction |
| **Externalized files** | State whose loss is expensive | Must be written to be kept |

**The test for externalizing:** *if losing this would make the agent redo work or repeat a mistake, it goes in a file.* Otherwise let compaction handle it.

**Compaction must preserve:** goal (verbatim) · decisions + why · findings + sources · **dead ends** · open questions · **exact identifiers**. Tune for recall first, precision second.

*(Module 4 Lessons 1, 4)*

---

## **Context assembly order**

```
┌─ STABLE — cached; high primacy attention ──────────────┐
│  1. System instructions                                │
│  2. Tool + skill definitions                           │
│  3. Canonical examples                                 │
│  4. Durable memory / conventions                       │
├─ ◆ CACHE BREAKPOINT ───────────────────────────────────┤
│  5. Compacted history summary                          │
├─ ◆ CACHE BREAKPOINT ───────────────────────────────────┤
│  6. Retrieved documents (ranked, edge-loaded)          │
│  7. Recent turns and tool results                      │
├─ VOLATILE — never cached; high recency attention ──────┤
│  8. Task state / plan and progress                     │
│  9. The immediate instruction                          │
└────────────────────────────────────────────────────────┘
```

Three rules: **never put anything volatile above anything stable** · **the task goes last, always** · **the middle is the cheap seats** — restate anything critical at position 9.

Drop by **value**, not by age. Edge-load ranked documents: `[1, 3, 5, 4, 2]`.

*(Module 8 Lesson 4)*

---

## **Agent, workflow, or neither?**

| | Workflow | Agent |
| :--- | :--- | :--- |
| Control flow | You write it | The model decides it |
| Cost | Predictable | Variable |
| Debugging | It's just code | Traces and interpretation |

> **If you can draw the flowchart, build the flowchart.** The moment it needs a box saying "figure out what to do next," you have an agent.

Most production systems are **workflows with an agentic step or two inside them**.

*(Module 5 Lesson 1)*

---

## **Loop design**

**Five components, all required:** trigger · **goal as a verifiable end state** · actions · verification · memory.

**Verification tiers** — prefer the lowest available:

| Tier | What | Use |
| :--- | :--- | :--- |
| 1 | Deterministic (tests, schema, row count) | Always, if you can design for it |
| 2 | Separate judge model + rubric | Qualitative goals; calibrate it |
| 3 | Human checkpoint | Irreversible / outward-facing actions |
| 4 | Agent self-report | **Never sufficient alone** |

**Five guardrails, all required:** iteration cap · token budget · circuit breaker on tool errors · **no-progress detection** · escalation carrying real state.

> Cost caps stop a *runaway* loop eventually. No-progress detection stops a *stuck* loop immediately.

*(Module 8 Lesson 2 · `code/examples/03_agent_loop.py`)*

---

## **Orchestration pattern**

| Pattern | Use when | Cost | Signature failure |
| :--- | :--- | :--- | :--- |
| **Single agent** | Try this first | 1× | — |
| **Fan-out** | Genuinely independent tasks | ~N× | Unspecified partial-failure policy |
| **Pipeline** | Each stage needs the last | ~N× | Cascade poisoning |
| **Debate** | High-stakes, experts differ | ~1.2–2.5× | Judge prefers style over correctness |
| **Supervisor** | Cross-domain specialists. **2026 default** | ~(N+1)× | Over-delegation into unfinishable slices |
| **Swarm** | 50+ parallel, unpredictable | Unbounded | Population explosion |

**The only question that justifies multi-agent:** *which work generates a lot of tokens whose details the coordinator doesn't need?*

**Handoff contract:** narrow question in · schema out · **mandatory `gaps` field** · per-sub-agent permissions.

*(Module 8 Lesson 3)*

---

## **Capability packaging**

| Use | When |
| :--- | :--- |
| **Plain tool** | One function, your codebase, this agent |
| **MCP server** | An external *system*, especially if several agents need it |
| **Agent Skill** | A *procedure*, used sometimes, shouldn't cost context when unused |
| **AGENTS.md** | Ambient repo knowledge every agent needs |
| **System prompt** | Behavior applying to every turn of this agent |

**The deciding question:** *"If the agent never does this task, should I still pay for these tokens?"* If no → skill.

*(Module 5 Lesson 4)*

---

## **Security**

> **Read untrusted content · hold private data · act outward — pick two.**

**Reduces likelihood** (necessary, not sufficient): delimiters · instruction hardening · input classifiers · canaries.

**Contains damage** (this is where security lives): least privilege · **egress allow-list** · sandboxing · human gates on irreversible actions · separated trust domains with a **schema** boundary · behavioral monitoring · output filtering.

> **Injection is a capability amplifier. With no capability, there is nothing to amplify.**

Audit the **combination**, not each addition. Red-team cases belong in CI.

*(Module 6 Lesson 3 · `code/examples/06_security.py`)*

---

## **Evaluation**

**Trajectory dimensions**, scored separately — a single score says it got worse; six say *which part*:

`tool_selection` · `argument_extraction` · `result_utilization` · `error_recovery` · `plan_coherence` · `task_completion`

**Judge calibration:** label 50–100 by hand → run the judge → measure kappa → **fix the rubric** if low → recheck after any change. Design against **position**, **verbosity**, and **self-preference** bias.

> 80% raw agreement can mean **zero** signal — a judge that always says PASS scores 80% against 8-good/2-bad labels and catches nothing.

**Stratify** across easy / hard / edge / adversarial / every production failure to date.

*(Module 6 Lesson 1 · `code/examples/05_evaluation.py`)*

---

## **Autonomy levels**

| Level | Agent | Human |
| :--- | :--- | :--- |
| 1 | Proposes | Executes |
| 2 | Executes sandboxed | Approves before effect |
| 3 | Executes | Reviews after |
| 4 | Executes | Samples and audits |

**Promote on evidence** — first-pass success and escalation rates. **Demote willingly.** The honest promotion signal is *approval with no substantive edits*, not approval.

*(Module 8 Lesson 3)*

---

## **The four that don't change**

1. **Context is finite and degrades.**
2. **Verification must live outside the agent.**
3. **Capability must be scoped.**
4. **You can't improve what you can't measure.**
