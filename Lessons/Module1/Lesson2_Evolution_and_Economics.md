# **Module 1, Lesson 2: The Evolution and Economics of Context**

### Building on What We've Learned

We've defined context and seen that it's the main lever on model behavior. Now we look at how context is managed in a real application, why models can't just know things, and the economics that constrain every design decision you'll make.

The economics section matters more than it used to. When a request was one model call, cost was an afterthought. When a request is an agent running fifty turns, cost is an architectural constraint.

### Learning Objectives

By the end of this lesson, you will be able to:
*   **Describe** the progression from stateless prompts to agent loops.
*   **Explain** what a knowledge cutoff is and why it makes retrieval necessary.
*   **Analyze** the trade-offs between context size, cost, latency, and quality.
*   **Calculate** the cost of an agent run, including the effect of prompt caching.

---

### **1. From Stateless Prompts to Agent Loops**

**Stage 1: The stateless prompt.**
Early interactions were stateless. One self-contained prompt in, one response out, no memory.

```
> ask_ai "Translate 'hello' to French."
"Bonjour"

> ask_ai "What language was that?"
"I'm sorry, I don't have the context of our previous conversation."
```
Cheap and simple; barely useful.

**Stage 2: The conversation window.**
Chat applications work by resending the conversation on every turn. The model doesn't "remember" — your application rebuilds its memory each time.

*   **User:** "Who was the first person on the moon?"
    ```json
    { "messages": [{"role": "user", "content": "Who was the first person on the moon?"}] }
    ```
*   **Model:** "Neil Armstrong."
*   **User:** "What was the name of his spacecraft?"
    ```json
    { "messages": [
        {"role": "user", "content": "Who was the first person on the moon?"},
        {"role": "assistant", "content": "Neil Armstrong."},
        {"role": "user", "content": "What was the name of his spacecraft?"}
    ]}
    ```
The model could answer the second question only because we resent the first exchange.

**Stage 3: The agent loop.**
This is where the economics change shape. An agent doesn't make one call per user request — it makes many, each one carrying the accumulated history *plus* every tool result so far.

```
Turn 1:  [instructions + tools + query]                            → tool call
Turn 2:  [instructions + tools + query + result 1]                 → tool call
Turn 3:  [instructions + tools + query + results 1-2]              → tool call
...
Turn 30: [instructions + tools + query + results 1-29]             → answer
```

Look at the shape of that: **the context grows on every turn, and you pay for the whole thing each time.** A single agent task routinely consumes 50–100× the tokens of a single chat turn. This is not a rounding error, and it's the reason the rest of this course spends so much time on what to *remove* from context.

---

### **2. Knowledge Cutoffs**

Every model's knowledge is a snapshot of its training data, frozen at a **knowledge cutoff**. Ask about events after that date and it cannot answer from memory — it's a historian who retired on a specific day.

Two nuances matter more than the basic fact:

*   **Models are unreliable about their own cutoff.** They will often state a date confidently and incorrectly, because that date is itself just training data.
*   **Coverage before the cutoff is uneven.** A model may know a well-documented public event thoroughly and know nothing about your company's product that launched the same week. "Before the cutoff" is not the same as "known."

> **Pro-Tip: Never trust, always verify**
> If factual accuracy matters, the only reliable approach is to supply the facts yourself through context. That's the entire premise of retrieval, which we cover in Module 3.

This is the single biggest structural reason context engineering exists: it is how you get up-to-date, proprietary, and domain-specific information into a system that cannot learn it.

---

### **3. The Economics of Context**

Everything ties back to **tokens**. A token is roughly ¾ of an English word. Models read, process, and bill by the token.

**The three costs:**

*   **Money.** You pay for input tokens and (more expensively) output tokens. More context, higher bill.
*   **Latency.** More input tokens means more time before the first token comes back. In an agent loop, that latency multiplies by the number of turns.
*   **Quality.** Bigger is not better. An oversized context padded with irrelevant material measurably degrades accuracy — an effect known as **context rot** (Module 4, Lesson 1).

That third one is the counterintuitive one, and it's what makes this an engineering discipline rather than a budgeting exercise. If more context were merely expensive, you'd just pay. It's also *worse*.

**The goal is information density: the most signal per token.**

---

### **4. Prompt Caching: The Lever That Changes the Math**

Modern APIs let you cache a prefix of your prompt. On a cache hit, those tokens bill at roughly **10% of the normal input rate**; writing to the cache costs a small premium (typically ~1.25×).

For an agent loop this is transformative, because the expensive, unchanging part of your context — system instructions, tool definitions, examples — is identical on all fifty turns.

**But there is one rule that decides whether you get the benefit at all:**

> **A cache prefix is valid only up to the first byte that changed.**

Put a timestamp, a request ID, or a session counter near the top of your prompt and you invalidate everything after it, on every single call. You will pay full price for a context you believe is cached, and the bug is invisible — nothing errors, the bill is just four times higher than your estimate.

**The rule that follows: order your context from most stable to most volatile.**

```
  stable   →  system instructions
              tool definitions
              few-shot examples
              ──── cache breakpoint ────
              retrieved documents
              conversation history
  volatile →  the current request
```

Two practical cautions: cache entries **expire** (commonly a few minutes by default, with longer options at a higher write rate), so a loop that fires one call every ten minutes may never hit the cache at all. And below roughly a 60% hit rate, the write premium can make caching cost *more* than not caching. Measure your hit rate; don't assume it.

---

### **5. Model Routing**

One more lever worth naming early, because it's the largest cost reduction available in most systems and it's usually left on the table.

Frontier models are dramatically more expensive than small ones — the spread across the current field is more than an order of magnitude. Most agent systems have steps that don't need frontier reasoning: classifying an intent, extracting fields from a document, deciding whether a retrieved chunk is relevant, summarizing a tool result.

**Route those to a cheap model. Route the hard synthesis to an expensive one.** A well-routed system commonly costs a fraction of a naive one at indistinguishable quality — and the routing logic is usually twenty lines of code.

---

### **Key Takeaways**

*   Chat works by **resending history** every turn. Agents compound this — context grows each turn and you pay for all of it, every time.
*   Models have **knowledge cutoffs**, are unreliable about what those cutoffs are, and have uneven coverage even before them.
*   Context has three costs: **money, latency, and quality**. The quality cost is what makes this engineering rather than budgeting.
*   **Prompt caching** cuts input costs by up to ~90%, but only if you order context **stable → volatile**. One volatile token near the top destroys the whole prefix.
*   **Model routing** — cheap models for easy steps — is usually the biggest available cost win.

### **Hands-On Task: The Napkin-Math of an Agent**

**Scenario.** You're costing out a customer-support agent.

*   **Frontier model:** $5.00 / 1M input tokens, $25.00 / 1M output tokens.
*   **Cached input reads:** 10% of the input rate. **Cache writes:** 1.25× the input rate.
*   **Small model:** $0.25 / 1M input, $1.25 / 1M output.

Your agent's context per turn:
*   System instructions + tool definitions: **2,000 tokens** (identical every turn)
*   Retrieved documents: **1,500 tokens** (fetched once, on turn 1, then carried)
*   Accumulated history and tool results: **grows by ~400 tokens per turn**
*   Output: **150 tokens per turn**

A typical conversation runs **8 turns**.

**Your Task:**

1.  **Cost one conversation with no caching.** Compute the input tokens per turn (remember the history grows), sum across 8 turns, and add output cost.
2.  **Cost it with caching.** The 2,000-token stable prefix is written once and read on turns 2–8. Recompute.
3.  **What's the saving,** in dollars and as a percentage? Was it larger or smaller than you expected before calculating?
4.  **Scale it.** 5,000 conversations per day. What's the monthly difference between the cached and uncached designs?
5.  **Route it.** Three of the eight turns are simple classification steps that a small model handles fine. Recompute the cached total with those three routed to the small model. Which lever — caching or routing — mattered more here, and would that ranking hold if the conversation ran 40 turns instead of 8?
6.  **Find the bug.** A colleague adds `"Current time: {timestamp}"` as the first line of the system instructions, for freshness. What happens to your cached cost, and how would you notice? Where should that line go instead?
