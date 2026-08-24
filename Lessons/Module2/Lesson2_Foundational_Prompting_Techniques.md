# **Module 2, Lesson 2: Foundational Prompting Techniques**

### Building on What We've Learned

Last lesson we built a prompt that *tells* the model what to do. This lesson is about *showing* it — the in-context learning techniques that remain the most reliable way to control output without touching model weights.

### Learning Objectives

By the end of this lesson, you will be able to:
*   **Differentiate** zero-shot, one-shot, and few-shot prompting.
*   **Choose** the right technique for a task's complexity, format requirements, and budget.
*   **Select** examples that teach the boundary rather than the average case.
*   **Recognize** when examples hurt rather than help.

---

### **1. Zero-Shot: The Basic Request**

**Zero-shot** means asking for a task with no examples, relying entirely on what the model already knows.

*   **Use for:** common, well-defined tasks — summarization, translation, simple classification.
*   **Pro:** simplest, cheapest, fewest tokens.
*   **Con:** output *format* is inconsistent even when the output *content* is right.

```python
system_prompt = "Classify the user's text as 'Positive', 'Negative', or 'Neutral'."
user_text = "The new UI is a bit clunky, but I love the new features."
# The model knows what sentiment analysis is. What it doesn't know is whether you
# want "Positive", "The sentiment is positive.", or "Mixed — leaning positive."
```

That last comment is the real failure mode. Zero-shot rarely fails at *understanding*; it fails at *conforming*.

---

### **2. One-Shot: A Single Perfect Example**

**One-shot** provides exactly one demonstration. Its main job is not to teach the task — it's to pin down the output format.

```python
messages = [
    # --- the one-shot example, as a prior exchange ---
    {"role": "user",      "content": "I absolutely adore the new design!"},
    {"role": "assistant", "content": "Positive"},
    # --- the real task ---
    {"role": "user",      "content": "The new UI is a bit clunky, but I love the new features."},
]
```

One well-chosen example buys you most of the format reliability that few-shot provides, for a fraction of the tokens. **When in doubt, start here rather than at zero.**

---

### **3. Few-Shot: Teaching Nuance**

**Few-shot** provides several examples (typically 2–5). It's how you teach judgment calls, edge cases, and house style — anything where the rule is easier to demonstrate than to state.

```python
examples = [
    {"role": "user", "content": "I can't log in."},
    {"role": "assistant", "content": "Technical"},

    {"role": "user", "content": "How do I upgrade my plan?"},
    {"role": "assistant", "content": "Billing"},

    # The important one: superficially technical, actually feedback.
    {"role": "user", "content": "Your app is so slow and unresponsive sometimes."},
    {"role": "assistant", "content": "Feedback"},
]
```

That third example is doing all the work. Without it, a zero-shot model classifies "your app is slow" as Technical every time — reasonably, since it mentions performance. The example is faster and more reliable than any sentence you could write explaining the distinction.

---

### **4. Choosing Good Examples**

Example quality dominates example quantity. The single most useful reframing:

> **Don't demonstrate the average case. Demonstrate the boundary.**

The model already handles the obvious cases. Your examples should spend their token budget on the cases where it would otherwise get it wrong.

*   **Quality over quantity.** Three diverse, well-chosen examples beat ten near-duplicates — and cost a third as much.
*   **Cover the edges.** Include the case you got wrong in production last week. That's your best example, and it's free.
*   **Watch for bias.** If every "engineer" example uses he/him, the model will replicate that. Examples teach patterns you didn't intend as reliably as ones you did.
*   **Be perfectly consistent in format.** The model learns your structure at least as strongly as your content. One example with a trailing period teaches "sometimes a trailing period."
*   **Order matters at the margins.** With a strong tail example, put it last — recency helps. Don't over-tune this; if output depends heavily on example ordering, your examples are too weak.

> **Pro-Tip: Start at zero, escalate only as needed**
> Zero-shot → one-shot → few-shot. Each step costs tokens on *every single call*, forever. Escalate when a measurable failure justifies it — and this is exactly the kind of change your eval set (Module 6) exists to adjudicate.

---

### **5. When Examples Hurt**

Few-shot is not free upside, and three cases are worth knowing.

**A. With reasoning models, on reasoning tasks.**
Models that produce extended internal reasoning before answering often perform *worse* with elaborate few-shot examples on hard reasoning problems — the examples pull them toward imitating a demonstrated path rather than working the problem. For these models on these tasks, prefer a clear statement of the task and the output format, and let the model reason. Keep few-shot for **format and style**, where it still helps everywhere.

**B. When the examples become the ceiling.**
Show three examples of two-sentence answers and you will get two-sentence answers — including when a question genuinely needs five. Examples don't just guide, they **bound**. If your outputs feel oddly uniform, look at your examples before you look at the model.

**C. When a schema would do it better.**
If your entire reason for using few-shot is to enforce a JSON shape, use a structured-output feature instead (Lesson 3). A schema *guarantees* what examples merely encourage — and it costs no tokens per call.

---

### **Key Takeaways**

*   **Zero-shot:** cheapest; fails on format consistency more than on comprehension.
*   **One-shot:** most format reliability per token. A good default when zero-shot is inconsistent.
*   **Few-shot:** teaches nuance and edge cases that are easier to show than to state.
*   **Demonstrate the boundary, not the average.** Your best example is last month's production failure.
*   Examples can **hurt**: on reasoning tasks with reasoning models, by capping output variety, and where a schema would be strictly better.

### **Hands-On Task: From Zero to Few-Shot**

**Scenario.** You're building a "Code Explainer" that describes a block of code in one plain-English sentence.

**Part A — Escalate deliberately.**

1.  **Zero-shot.** Write a system prompt and pass it `def add(a, b): return a + b`. Note the exact format you get back. Run it three times — is it identical each time?
2.  **One-shot.** Add one perfect example. Does the format stabilize? What *specifically* changed?
3.  **Few-shot.** Add two or three more, ranging from simple to complex (e.g. a list comprehension, a decorator, a small class). Test on something none of them resemble.

**Part B — Break it deliberately.** Feed your few-shot prompt a 40-line class with three methods and a nontrivial invariant. Does it still produce one sentence? Is that sentence useful, or did your examples cap the output below what the input needed?

**Part C — Design the boundary example.** Your explainer is now in production and consistently mishandles code with side effects: given a function that both computes *and* writes to a database, it describes only the computation. Write the single few-shot example that fixes this, and explain in one line what makes it the *right* example rather than just *an* example.
