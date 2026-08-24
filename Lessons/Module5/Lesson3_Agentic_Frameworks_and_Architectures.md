# **Module 5, Lesson 3: Agentic Frameworks and Architectures**

### Building on What We've Learned

You can define tools and run a loop by hand. That's instructive, and for a while it's also sufficient. This lesson covers the architectures worth knowing, the frameworks that implement them, and — importantly — how to adopt a framework without letting it become the thing you can't replace.

### Learning Objectives

By the end of this lesson, you will be able to:
*   **Compare** the major agent architectures and choose one for a task.
*   **Identify** what frameworks provide, and what they cost you.
*   **Structure** framework usage so you can migrate off it.
*   **Build** a minimal agent loop from scratch, so you know what's underneath.

---

### **1. The Architectures**

| Architecture | How it works | Good for | Weakness |
| :--- | :--- | :--- | :--- |
| **ReAct** | Reason → act → observe, re-planning every step | Exploratory work; unknown path | Wanders; loses the thread on long tasks |
| **Plan-and-Execute** | Full plan up front, then execute the steps | Predictable, decomposable workflows | Can't adapt when step 2 invalidates step 7 |
| **Plan-Act-Replan** | Plan, execute a few steps, re-plan against results | Most real work | More model calls than either pure form |
| **Reflexion** | ReAct plus an explicit self-critique after each attempt | Quality-graded tasks | Self-critique is weak without an external signal |
| **Router / workflow** | Deterministic code calls models at fixed points | Known steps; most production systems | Not an agent — and that's usually the point |

**In practice, plan-act-replan is what most good agents do**, whether or not the framework calls it that. Pure Plan-and-Execute is too rigid for anything with surprises, and pure ReAct drifts on anything long. The middle — commit to a plan, execute a few steps, check whether the plan still makes sense — is where most real systems land.

**A note on ReAct's stopping condition.** ReAct as originally described terminates when the model decides it's done. That's the weakness Module 8 fixes with external verification. When you see ReAct in a framework, check what actually ends the loop — it is very often the model's own judgment, and that is very often not what you want.

---

### **2. What Frameworks Give You, and What They Cost**

Frameworks handle the boilerplate: converting functions to schemas, running the loop, managing state, streaming, retries, and often tracing.

**The current landscape** (expect the names to churn; the categories won't):

*   **Graph-based orchestrators** (LangGraph and similar). You define agents as a state machine — nodes and edges with explicit state. More verbose than a simple loop, and that verbosity buys you something real: durable execution, resumability after a crash, and human-in-the-loop pauses. Worth it for long-running or approval-gated work.
*   **Vendor agent SDKs** (Claude Agent SDK, OpenAI Agents SDK, Google ADK). Tightly integrated with one provider's model, tool use, and features. Typically the fastest path to a working agent, with the tightest coupling.
*   **Multi-agent frameworks** (Microsoft Agent Framework, which absorbed AutoGen; CrewAI). Conversation patterns and role-based teams. Useful when you genuinely need the patterns from Module 8, Lesson 3 — and overhead when you don't.
*   **Data-centric frameworks** (LlamaIndex). Strongest on ingestion, indexing, and retrieval, with agent capabilities layered on.

**What they cost you:**

*   **Debuggability.** When something goes wrong inside a framework's loop, you're reading someone else's stack trace and inferring their prompt. Frameworks that let you see and override the actual prompt sent are worth substantially more than ones that don't.
*   **Hidden prompts.** Many frameworks inject their own instructions into your context. You are paying for tokens you didn't write and may not have read.
*   **Lock-in.** Control flow threaded through a framework's abstractions is expensive to unwind. Section 4 is about containing this.

> **A defensible default: build the loop yourself first.** It's about a hundred lines (section 3), it teaches you exactly what a framework is doing, and it means you adopt a framework to solve a problem you've *felt* rather than one you've read about. Then adopt one when you need durable execution, resumability, or a well-tested orchestration pattern — those are genuinely hard to build well.

---

### **3. A Minimal Agent Loop**

Worth writing once. Everything else is this with more features.

```python
def run_agent(goal, tools, max_iterations=20, token_budget=500_000):
    messages = [{"role": "user", "content": goal}]
    tokens_used = 0

    for i in range(max_iterations):
        if tokens_used > token_budget:
            return escalate("token budget exhausted", messages)

        response = model(
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=[t.schema for t in tools],
        )
        tokens_used += response.usage.total_tokens
        messages.append({"role": "assistant", "content": response.content})

        tool_calls = [b for b in response.content if b.type == "tool_use"]
        if not tool_calls:
            break                                  # model produced a final answer

        results = []
        for call in tool_calls:
            try:
                out = dispatch(tools, call.name, call.input)
            except Exception as e:
                out = {"error": str(e), "hint": recovery_hint(call.name, e)}   # never raise
            results.append({"type": "tool_result", "tool_use_id": call.id, "content": out})

        messages.append({"role": "user", "content": results})

        if len(messages) > COMPACT_THRESHOLD:       # Module 4, Lesson 4
            messages = compact(messages)

    return verify_and_return(goal, messages)        # Module 8, Lesson 2 — external check
```

Five things in there are the difference between a demo and something you'd run unattended, and they're all in the harness rather than the model: the **iteration cap**, the **token budget**, **errors returned rather than raised**, **compaction**, and **external verification** at the end. Note that the `break` on "no tool calls" is *not* the success condition — it exits the loop, and `verify_and_return` decides whether that exit was a success.

---

### **4. Adopting a Framework Without Marrying It**

Frameworks churn fast. Structure your code so replacing one is a week, not a quarter.

```
your_code/
  agent/
    goals.py        # goal definitions and verification — yours
    tools/          # tool implementations — yours, plain functions
    context.py      # what goes in the window — yours
    policy.py       # permissions and limits — yours
    runtime.py      # ← the ONLY file that imports the framework
```

**Keep in your own code:** tool implementations (plain functions, framework-agnostic), context assembly, permission and budget policy, verification logic, and your evals.

**Let the framework own:** the loop mechanics, state persistence, streaming, retries.

The test: **if you deleted the framework, how much of your business logic would go with it?** If the answer is "most of it," the abstraction leaked. That's not an argument against frameworks — it's an argument for confining them to one file.

---

### **Key Takeaways**

*   Five architectures matter: **ReAct, Plan-and-Execute, Plan-Act-Replan, Reflexion, and workflow/router.** Most good agents are effectively **plan-act-replan**.
*   ReAct's stopping condition is **the model's own judgment**. Check what actually ends your framework's loop.
*   Frameworks buy boilerplate, durable execution, and resumability; they cost **debuggability, hidden prompts, and lock-in**.
*   **Write the loop yourself once.** It's ~100 lines and it tells you what you're buying.
*   A production loop needs five harness features: **iteration cap, token budget, non-raising errors, compaction, external verification.**
*   Confine the framework to **one file**. Keep tools, context, policy, verification, and evals in code you own.

### **Hands-On Task: Architecture and Insulation**

**Part A — Choose an architecture.** For each, pick one and justify it, naming the specific property of the task that decides it.

1.  **Travel booker.** Search flights → search hotels for those dates → check rental cars → confirm with the user. Predictable and linear.
2.  **Autonomous researcher.** "What's the current state of AI in healthcare?" Search, read, follow links, identify themes, synthesize. The path is unknown at the start.
3.  **Automated coder.** "Write a Python script that GETs an API and saves the result." Write, run, check errors, save.
4.  **Incident responder.** Alert fires. Check dashboards, correlate with deploys, form a hypothesis, test it, either mitigate or escalate. Some steps are fixed; the middle depends entirely on what's found.
5.  **Invoice processor.** 200 invoices/day: extract fields, validate against the PO, flag discrepancies, queue for approval.

**Part B — Find the workflow hiding in the agent.** For scenarios 1 and 5, write the workflow version in pseudocode. Then identify the *one* step in each that genuinely benefits from model reasoning, and explain why the rest shouldn't be model-driven.

**Part C — Insulate.** You've built scenario 4 on a framework. Leadership wants an evaluation of switching frameworks next quarter.

1.  List which parts of your system should be framework-independent.
2.  For each, say what a naive implementation would have coupled to the framework, and what the insulated version looks like.
3.  Name the one piece you'd accept coupling on, and justify why re-implementing it isn't worth the insurance.
