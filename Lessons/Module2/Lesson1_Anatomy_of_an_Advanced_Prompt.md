# **Module 2, Lesson 1: The Anatomy of an Advanced Prompt**

### Building on What We've Learned

Module 1 established that context is the world you build for a model, and that the system prompt is one component of it. This module zooms into that component — because while it's a smaller share of the context than it used to be, it's still the piece that governs *how the model uses everything else*.

An advanced system prompt is not a paragraph of politeness. It's a specification.

### Learning Objectives

By the end of this lesson, you will be able to:
*   **Differentiate** the roles of the system prompt and the user turn.
*   **Craft** a system prompt with a clear persona, rules, and constraints, at the right altitude.
*   **Transform** a vague question into a specific command.
*   **Recognize** what belongs in a system prompt and what belongs elsewhere.

---

### **1. System vs. User: Setting the Stage**

Think of a model interaction as a play.

*   The **system prompt** is the direction given to the actor before the curtain rises: who they are, what the rules of the world are, what they must never do. It persists across the entire performance.
*   The **user turn** is a line of dialogue from another actor — immediate, transient, and to be responded to *within* the character's constraints.

This distinction is also a **trust boundary**, and that's the part people underweight. The system prompt is authored by you. User turns and tool results are not. Every major API separates them for exactly this reason, and models are trained to weight system instructions more heavily. It's not a hard guarantee — Module 6 covers why — but it is the first structural line between your instructions and someone else's input.

**Code Example: the power of a system prompt**

```python
import anthropic
client = anthropic.Anthropic()

system_prompt = (
    "You are a sarcastic, world-weary robot detective from a 1940s noir film. "
    "You answer every question reluctantly and with a cynical tone."
)

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=512,
    system=system_prompt,                       # ← separate parameter, not a message
    messages=[{"role": "user", "content": "I need help finding my lost keys."}],
)

# "Keys, huh? Of all the circuits in all the gin joints in all the world, you had
#  to lose your keys. Alright, spill it. Where'd you last see 'em?"
print(response.content[0].text)
```

> **API note:** Anthropic's Messages API takes `system` as its own top-level parameter; OpenAI-style APIs put it as the first message with `role: "system"` (or `"developer"` in newer versions). The concept is identical. Keep it in *one* place either way — splitting instructions between a system parameter and a "reminder" user message is a common source of contradictory behavior.

---

### **2. The Three Components of a Strong System Prompt**

**A. Persona — who to be.**
A persona gives the model a coherent frame for reasoning, not just a voice.
*   **Weak:** "Be friendly."
*   **Strong:** "You are a high-school chemistry teacher who loves making hard topics approachable. Use analogies and plain language."

The strong version constrains vocabulary, explanation depth, and what counts as a good answer — all at once, in one sentence. That efficiency is why personas earn their tokens.

**B. Rules — the unbreakable laws.**
Non-negotiable directives. Use structure and emphatic verbs.
```markdown
# RULES
1. NEVER invent products or prices.
2. You MUST use `search_products` if the user names a specific item.
3. If a product isn't in the search results, say so plainly.
```

Two things make rules work: **there are few of them**, and **each is checkable**. A list of thirty rules is a list the model will apply inconsistently — and it's usually a sign of the altitude problem from Module 1, Lesson 3.

**C. Constraints — the boundaries of the output.**
*   **Format:** "Respond with a single valid JSON object." / "Your answer must be one paragraph."
*   **Scope:** "Use only the provided documents." / "Under 100 words."

> **The negative-instruction trap.** "Don't be verbose" is weaker than "Answer in at most three sentences." "Don't make things up" is weaker than "Every claim must cite a source from the context; if you cannot cite it, say you don't know." **State the behavior you want, not the one you don't** — a positive instruction gives the model a target, a negative one gives it only a thing to avoid while it improvises the rest.

---

### **3. What Does *Not* Belong in a System Prompt**

As important as what goes in. Putting these in a system prompt is one of the most common sources of systems that work in month one and rot by month six:

| Don't put this in the prompt | Put it here instead | Why |
| :--- | :--- | :--- |
| Business policy (refund rules, SLAs, pricing) | Retrieved knowledge | It changes without an engineer, and the owner can't see the prompt |
| Per-user facts (tier, order history, preferences) | A tool call, or memory | The prompt can't know them; asking the model to reason about them is asking it to guess |
| Long procedures (a 40-step workflow) | An on-demand skill (Module 5, Lesson 4) | Loading all 40 steps on every run costs tokens on every run that isn't that task |
| Anything volatile (timestamps, request IDs) | The end of the context, or a tool | It destroys your cache prefix (Module 1, Lesson 2) |

**The test:** if a non-engineer owns the information, or it changes on a different cadence than your code, it doesn't belong in the prompt.

---

### **4. From Vague Query to Specific Command**

The final piece is phrasing the request as a **command**, not a question. A question invites information retrieval; a command specifies a task and a shape.

*   **Vague:** "What are the differences between Python and JavaScript?"
*   **Specific:** "Create a Markdown table comparing Python and JavaScript. Columns: Feature, Python, JavaScript. Rows: typing discipline, primary use case, concurrency model, package ecosystem."

The second leaves nothing to interpretation: what to produce, what shape, what to cover. When you're chaining a model's output into other software, this is the difference between a parser that works and a parser that works most of the time.

---

### **Key Takeaways**

*   The **system prompt** sets character and rules and is a **trust boundary**; the **user turn** is the immediate, untrusted task.
*   Strong system prompts have a clear **persona**, few **checkable rules**, and explicit **constraints**.
*   **State the behavior you want, not the one you don't.** Positive instructions give the model a target.
*   Business policy, per-user facts, long procedures, and volatile values **do not belong in the prompt**.
*   Phrase requests as **commands** that specify content and shape.

### **Hands-On Task: Design a Meeting Summarizer**

**Scenario.** You're building an agent that turns messy raw meeting transcripts into clean structured summaries.

**Part A — Write the system prompt.** It should include:

1.  **A persona** — who is this, and what do they care about?
2.  **Instructions** — a clear process: identify topics discussed, extract decisions, then list action items with owners.
3.  **Constraints** — exact output format, with three Markdown sections: `## Summary`, `## Key Decisions`, `## Action Items`.
4.  **A rule for the hard case:** an action item is mentioned but nobody is clearly assigned. Say exactly what the model should do — a guess is the wrong answer, and so is silently dropping it.

**Part B — Keep it out.** Your colleague suggests adding these to the prompt. For each, say whether it belongs there, and if not, where it goes:

*   "Sarah is the VP of Engineering, Marcus runs Product, Priya leads Design."
*   "Never include anything discussed after someone says 'off the record'."
*   "Our company uses 'workstream' rather than 'project'."
*   "The transcript is from the meeting on {date} in room {room}."

**Part C — Rewrite the negatives.** Find every negative instruction in your Part A prompt and rewrite it as a positive one. If you have none, you probably wrote *"Don't include filler"* somewhere and phrased it politely — check again.
