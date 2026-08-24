# **Module 2, Lesson 3: Advanced Prompting Strategies**

### Building on What We've Learned

We've covered prompt anatomy and in-context learning. Now we cover the strategies that make models reason reliably and emit data your software can trust — and how both changed once reasoning models and structured outputs became standard.

### Learning Objectives

By the end of this lesson, you will be able to:
*   **Apply** Chain-of-Thought, and explain when native reasoning has made it unnecessary.
*   **Design** a generate → critique → revise loop, and identify its central weakness.
*   **Enforce** structured output with a schema rather than an instruction.
*   **Decompose** a complex task into a chain of reliable steps.

---

### **1. Chain-of-Thought: "Show Your Work"**

**Chain-of-Thought (CoT)** asks the model to lay out its reasoning before the answer. Externalizing the steps makes the model less likely to make a leap, and makes the output debuggable.

```python
problem = ("John has 5 apples. He buys 3 boxes with 4 apples each. "
           "He gives away 2. How many does he have?")

prompt = f"""{problem}

Think step by step, then give the final answer on its own line prefixed with 'ANSWER:'.
"""

# Step 1: John starts with 5 apples.
# Step 2: 3 boxes × 4 apples = 12 apples.
# Step 3: 5 + 12 = 17.
# Step 4: 17 − 2 = 15.
# ANSWER: 15
```

Note the `ANSWER:` prefix — CoT produces reasoning you have to *parse past*. Always specify a delimiter so your code can extract the answer without regexing prose.

**What changed: native reasoning.**
Frontier models now do this internally. Given a reasoning budget, they produce extended structured reasoning before responding — trained for the purpose rather than coaxed by a phrase.

This changes the advice:

| Situation | What to do |
| :--- | :--- |
| Reasoning model, hard problem | **Don't add "think step by step."** Allocate reasoning budget instead. Explicit CoT instructions can constrain a model that reasons better on its own. |
| Reasoning model, simple task | Keep the reasoning budget low or off. You pay for reasoning tokens. |
| Small or fast model | **CoT still helps a lot.** This is where the classic technique earns its keep. |
| You need the reasoning *visible* to users | Ask for it explicitly, whatever the model — internal reasoning isn't always exposed, and when it is it's not written for an audience. |

> **The durable principle underneath:** hard problems need computation before commitment. Whether that computation is prompted or native is an implementation detail that will keep changing.

---

### **2. Self-Critique Loops — And Their Limit**

A powerful pattern for qualitative work: generate, critique, revise.

```python
# Step 1 — draft
first_draft = "Our system is good. Users like it. We should invest more."

# Step 2 — critique (fresh call, critic persona)
critique_prompt = f"""You are a demanding editor. Identify specific weaknesses in
the text below. Focus on vague language and unsupported claims. List each weakness
as a bullet with a concrete suggested fix.

<text>
{first_draft}
</text>
"""

# Step 3 — revise
final_prompt = f"""Rewrite the original text, addressing every point in the critique.

<original>{first_draft}</original>
<critique>{critique_from_step_2}</critique>
"""
```

This genuinely improves output on writing, planning, and design tasks. **But there's a ceiling you need to know about:**

> A model critiquing its own work shares its own blind spots. If it didn't know a fact was wrong when it wrote it, it won't know when it reviews it. Self-critique reliably improves **style, structure, and completeness against stated criteria**. It does not reliably catch **factual errors or logical mistakes** the model was already confident about.

Three things strengthen it, in ascending order of effectiveness:

1.  **Give the critic a rubric**, not a vibe. "Find weaknesses" produces generic feedback; "check each claim for a supporting citation, flag any sentence over 30 words, verify every number appears in the source data" produces actionable feedback.
2.  **Use a fresh context.** Don't append the critique to the drafting conversation — a model looking at its own reasoning trace tends to defend it. A clean call with just the text and the rubric is a genuinely different reviewer.
3.  **Bring in an external signal.** A test suite, a schema validator, a linter, a retrieval check against source documents. **This is the only tier that catches the errors self-critique structurally can't** — and it's the bridge to verification in Module 8, Lesson 2.

---

### **3. Structured Output: Use a Schema, Not a Request**

For application code you need parseable output. There is a hierarchy of reliability here, and most teams are one step below where they should be:

| Approach | Reliability | Notes |
| :--- | :--- | :--- |
| Asking nicely for JSON in the prompt | Low | Works until the model adds ```` ```json ```` fences, a preamble, or a trailing comment |
| Few-shot examples of JSON | Medium | Better, but still probabilistic — and costs tokens on every call |
| **A schema the API enforces** | **High** | The output is *constrained* to be valid, not encouraged |

**Use the schema.** Modern APIs enforce a JSON Schema (via structured-output parameters, or by defining the output shape as a tool the model must call). This is a categorical difference, not an incremental one: you move from "usually parses" to "parses."

```python
import anthropic
client = anthropic.Anthropic()

review_schema = {
    "name": "record_review_analysis",
    "description": "Record the extracted pros and cons of a product review.",
    "input_schema": {
        "type": "object",
        "properties": {
            "pros":      {"type": "array", "items": {"type": "string"}},
            "cons":      {"type": "array", "items": {"type": "string"}},
            "sentiment": {"type": "string", "enum": ["positive", "negative", "mixed"]},
        },
        "required": ["pros", "cons", "sentiment"],
    },
}

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    tools=[review_schema],
    tool_choice={"type": "tool", "name": "record_review_analysis"},   # force it
    messages=[{"role": "user", "content": f"Analyze this review: {text}"}],
)

analysis = response.content[0].input        # already a dict, guaranteed to fit the schema
```

**Two design notes that matter more than the syntax:**

*   **The schema is prompt surface.** Field names and descriptions are read by the model. `{"sentiment": {"description": "overall sentiment, weighing the reviewer's conclusion more heavily than individual complaints"}}` steers behavior. Treat schema descriptions as instructions, because they are.
*   **A schema constrains shape, not truth.** `sentiment: "positive"` is guaranteed to be one of your three enum values. It is not guaranteed to be *correct*. Validation is not verification.

---

### **4. Decomposition: The Meta-Strategy**

The most reliable way to make a hard task work is usually to stop asking one call to do it.

**One call, five jobs** — research, analyze, decide, format, verify — fails in a way that's hard to debug: you get a bad answer with no visibility into which job went wrong.

**Five calls, one job each** gives you something better than reliability — it gives you **localizability**. Each step can be tested, cached, retried, routed to an appropriately-sized model, and inspected in a trace.

```
[cheap model]  extract entities from document
       ↓
[cheap model]  classify each entity
       ↓
[frontier]     reason about the classified set
       ↓
[schema]       emit structured result
       ↓
[code]         validate against business rules
```

The cost is latency and orchestration complexity. The benefit is that when it breaks, you know where. This pattern is the direct ancestor of the loop and pipeline architectures in Module 8.

---

### **Key Takeaways**

*   **CoT** still helps small and fast models. For reasoning models, allocate a **reasoning budget** rather than instructing "think step by step" — and always specify a delimiter so your code can find the answer.
*   **Self-critique** improves style, structure, and completeness. It does **not** reliably catch factual errors the model was confident about — for that you need an external signal.
*   Use a **schema the API enforces**, not a polite request for JSON. Schema field descriptions are prompt surface; schema validity is not truth.
*   **Decompose.** One job per call buys you localizability — the ability to know *which* step failed.

### **Hands-On Task: The Multi-Step Meal Planner**

**Scenario.** *"I need a healthy, low-carb meal plan for 3 days. I don't eat fish."*

**Part A — Build the chain.**

1.  **Generate.** Write a prompt producing an initial 3-day plan against all the constraints. Say whether you'd use explicit CoT here and justify it by model type.
2.  **Critique.** Write a critic prompt with an explicit **rubric**, not "find problems." At minimum it should check: genuine low-carb status (hidden carbs — potatoes, rice, sauces), variety (not chicken six times), completeness (3 meals × 3 days), and the no-fish constraint.
3.  **Revise + structure.** Produce the final plan as a **schema-enforced** object: keys `Day1`–`Day3`, each with `Breakfast`, `Lunch`, `Dinner`, and each meal carrying `name`, `main_protein`, and `est_carbs_g`.

**Part B — Find what self-critique can't catch.** Your critic passes a plan containing a meal listed at 8g carbs that actually contains about 40g. Explain why the critic missed it, and design the **external check** that catches it. What does that check need access to?

**Part C — Route it.** Assign each of your three steps a model tier (cheap / frontier) and justify each choice in one line. Which step would you never route down, and why?
