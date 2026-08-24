# **Module 6, Lesson 2: Testing, Tracing, and Debugging**

### Building on What We've Learned

When traditional code fails, a stack trace tells you exactly where. When an LLM application fails, the cause is often a mystery. Did the prompt fail? The retriever? The generator? **Tracing** is the practice of observing the entire lifecycle of a request as it passes through your system. It's the "debugger" for LLM applications.

### Learning Objectives

By the end of this lesson, you will be able to:
*   **Explain** why tracing is essential for debugging multi-stage LLM applications.
*   **Analyze** a failure cascade in a RAG pipeline and in an agent trajectory.
*   **Instrument** an application using the OpenTelemetry GenAI conventions.
*   **Debug** methodically from a trace rather than by guessing at prompts.

---

### **1. The Challenge: Debugging a Black Box**

An LLM application is a pipeline of components. A failure in an early stage causes a cascade of failures in all subsequent stages.

**Scenario: A Common Failure Cascade**
*   **User Query:** "What was our revenue last quarter?"

**The Failure Flow:**
1.  **Retrieval (The Real Failure):** The retriever misunderstands "last quarter" and fetches the *Q1* 2024 financial report instead of the *Q2* report.
2.  **Generation (The Apparent Failure):** The Generator LLM receives the user's question ("...last quarter...") but its context *only* contains Q1 documents. It now has a conflict. It might:
    *   **Hallucinate:** Invent a number for Q2. (Low Faithfulness)
    *   **Answer Faithfully but Irrelevantly:** Give the correct number for Q1. (Low Answer Relevance)
    *   **Give Up:** State that it cannot find the answer for Q2. (The system still failed)

Without a trace, you would only see the final, incorrect answer. You might spend hours tweaking the Generator's prompt, when the real problem was with the Retriever.

---

### **2. LLM Observability: Lighting up the Black Box**

**LLM Observability** platforms are essential for serious development. They provide SDKs that automatically log the inputs and outputs of every major step in your pipeline.

**Popular Tracing Platforms:**
*   **LangSmith:** The most popular platform, tightly integrated with the LangChain framework.
*   **Phoenix (from Arize AI):** An open-source library that offers powerful tracing for local development.
*   **W&B Prompts (Weights & Biases):** Extends the popular ML experiment tracking platform to include LLM tracing.

**What a Trace Looks Like:**
These platforms give you a "waterfall" view of your request in a web UI.

```
▶️ AgentExecutor (Latency: 2.5s)
  ▶️ Retriever (Latency: 0.5s)
    *️⃣ Input:  "What was our revenue last quarter?"
    *️⃣ Output: [doc_q1_report, doc_q1_earnings_call_summary]  <-- CLICK TO INSPECT

  ▶️ Generator (LLM) (Latency: 2.0s)
    *️⃣ Input:  (A long prompt containing the Q1 docs)        <-- CLICK TO INSPECT
    *️⃣ Output: "Our revenue in Q1 was $5 million..."          <-- CLICK TO INSPECT
```

**Using a Trace to Debug:**
This view makes debugging methodical.
1.  **Start at the end:** Is the final output wrong?
2.  **Work backwards:** If the output is wrong, inspect the input to that step. Was the prompt to the Generator missing the correct information?
3.  **Find the source:** If the prompt was bad, inspect the step before it. Did the Retriever fail to fetch the correct documents? Yes.
4.  **Isolate the problem:** The problem is the Retriever. Now you can focus your efforts on improving the retrieval step, knowing it's the source of the failure.

For any production-level context engineering, using a tracing platform is non-negotiable.

---

### **3. OpenTelemetry: Tracing Stopped Being Vendor-Specific**

Through 2024 every observability vendor had its own SDK and its own schema, and switching meant re-instrumenting. That changed.

The **OpenTelemetry GenAI semantic conventions** define a standard vocabulary — `gen_ai.*` span and metric attributes — for model invocations, tool executions, agent runs, retrieval, and memory operations. A trace emitted by one tool is readable in any OTLP-compatible backend. Major coding agents now emit these directly.

**An agent run models as a small set of recognizable span types:**

```
gen_ai.agent   "incident_responder"           duration=142s  cost=$0.84
├── gen_ai.chat        model=… in=4.2k out=180  finish=tool_use
├── gen_ai.tool        name=search_logs        duration=1.2s  → 8.4k tokens
├── gen_ai.chat        model=… in=13.1k out=95  finish=tool_use
├── gen_ai.tool        name=get_deploys        duration=0.4s  → 300 tokens
├── gen_ai.agent       "log_researcher"        (sub-agent)    cost=$0.31
│   ├── gen_ai.tool    name=grep_logs          …
│   └── gen_ai.chat    …                       → returns 1.4k distillate
└── gen_ai.chat        model=… in=19.8k out=620 finish=end_turn
```

**Two caveats worth carrying:**

*   **The conventions are still pre-stable.** As of mid-2026 they've moved into their own repository but have not hit 1.0, so attribute names can still change. **Instrument through a thin wrapper you own** rather than sprinkling raw attribute names across your codebase — then a rename is one file.
*   **Traces contain everything.** Prompts, retrieved documents, tool arguments, and model outputs — which means PII, credentials, and customer data flow into your observability backend. Decide deliberately what you redact, and where.

**What to record beyond the defaults:** context token count *broken down by section*, cache hit rate, which retrieval strategy fired, compaction events, and the version of your prompts, tools, and harness. That last one is what lets you answer "what changed?" three weeks later — and you will be asked.

---

### **4. Debugging an Agent Trajectory**

Agents fail in ways a RAG pipeline can't, because they have a *history*. Four patterns are recognizable at a glance in a trace:

| Pattern | What you see | Usual cause |
| :--- | :--- | :--- |
| **Thrashing** | The same tool returning a result it already returned | The tool isn't returning what the agent needs, and nothing says so |
| **Context blowout** | Input tokens climbing steeply per turn | A tool returning huge results; no compaction |
| **Premature exit** | `finish=end_turn` while the goal is unmet | No external verification — the model decided it was done |
| **Silent tool failure** | A tool returns an error, the agent proceeds as if it succeeded | The error is unclear, or buried mid-context |

**The debugging procedure, in order:**

1.  **Start from the outcome.** Is it wrong, incomplete, or expensive?
2.  **Find the divergence point** — the first turn where the agent did something you wouldn't have.
3.  **Read that turn's full input.** Not your template — the actual assembled context. Was the needed information present? Was it in the low-attention middle? Was a tool error sitting there unaddressed?
4.  **Fix the cause, not the symptom.** If the information was missing, that's retrieval or context assembly. If it was present and ignored, that's positioning or prompt clarity. If the agent recovered badly from an error, that's the tool's error message.
5.  **Add it to the eval set** before you fix it — otherwise you can't tell whether the fix worked.

> **Detecting thrashing correctly is fiddlier than it looks.** Keying on *arguments* misses the common case — three rephrasings of a query are three genuinely different calls. Keying on the *tool name* over-fires — an agent reading ten different files is working, not thrashing. What is unambiguously wasted is **the same tool returning a result it has already returned**: three rephrasings that surface the identical five articles taught the agent nothing on calls two and three. (`Trace.thrashing()` in `code/ce/trace.py` implements exactly this.)

> **Pro-Tip: The most useful single line in your trace is the assembled context.**
> Most teams log the user query and the model output and not the thing in between. But the assembled context *is* what the model saw — everything else is inference about it. Log it, with a size breakdown by section, on every call. Storage is cheap; the alternative is debugging by imagination.

---

### **Key Takeaways**

*   **Tracing** shows the inputs and outputs of every component. Without it you are debugging by imagination.
*   Failures **cascade**: a retrieval problem surfaces as a generation problem, and you can waste days tuning the wrong stage.
*   **OpenTelemetry GenAI conventions** made traces portable across backends. They're pre-stable, so instrument through a wrapper you own — and decide what to redact, because traces carry everything.
*   Four agent failure patterns are visible at a glance: **thrashing, context blowout, premature exit, silent tool failure.**
*   Debug by finding the **divergence point** and reading the **actual assembled context** at that turn. Log it, with a per-section size breakdown, on every call.
*   **Add the failure to your eval set before fixing it.**

### **Hands-On Task: Find the Failure**

You are debugging an AI Agent using the trace below.
*   **User Goal:** "Send an email to bob@example.com summarizing the Q2 earnings report."

**The Trace:**
```
▶️ AgentExecutor
  ▶️ Tool: search_knowledge_base
    *️⃣ Input:  "Q2 earnings report"
    *️⃣ Output: [ "Q2 earnings were $10M, beating estimates..." ]
  ▶️ Tool: send_email
    *️⃣ Input:  { recipient: "bob@example.com", subject: "Q2 Report", body: "Q1 earnings were $8M..." }
    *️⃣ Output: { success: true }
```

**Part A — Find the failure.**
1.  What was the final result of the agent's work?
2.  Which component failed — the Planner (the model's reasoning) or a Tool?
3.  What was the specific error, and at which step did it originate?
4.  Name two harness changes that would prevent this class of failure, and say which one you'd ship first.

**Part B — Read an agent trace.** A research agent was asked to *"summarize our Q2 competitive landscape."*

```
gen_ai.agent "competitive_research"                     duration=310s  cost=$4.20
├── gen_ai.chat        in=3.1k   out=140   finish=tool_use
├── gen_ai.tool  search_docs("competitors")   → 24.0k tokens returned
├── gen_ai.chat        in=27.4k  out=110   finish=tool_use
├── gen_ai.tool  search_docs("competitor analysis") → 22.0k tokens
├── gen_ai.chat        in=49.8k  out=95    finish=tool_use
├── gen_ai.tool  search_docs("Q2 competitors")     → 23.0k tokens
├── gen_ai.chat        in=73.1k  out=120   finish=tool_use
├── gen_ai.tool  search_docs("market share Q2")    → 21.0k tokens
├── gen_ai.chat        in=94.5k  out=90    finish=tool_use
├── gen_ai.tool  get_financials("Q2")              → ERROR: "Invalid period format"
├── gen_ai.chat        in=94.8k  out=85    finish=tool_use
├── gen_ai.tool  get_financials("Q2 2026")         → ERROR: "Invalid period format"
├── gen_ai.chat        in=95.1k  out=80    finish=tool_use
├── gen_ai.tool  get_financials("2026-Q2")         → ERROR: "Invalid period format"
└── gen_ai.chat        in=95.4k  out=780  finish=end_turn
```

1.  **Name every failure pattern** from section 4 that appears here. There are at least three.
2.  **Where is the divergence point** — the first turn where you'd have done something different?
3.  **The final answer will be confident and cite no financial data.** Explain the two independent reasons a reader can't trust it.
4.  **Prescribe four fixes**, each tied to a specific line in the trace. For each, say which harness layer it belongs to.
5.  **One of your fixes is worth more than the other three combined.** Which, and why? 