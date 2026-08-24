# **Module 1, Lesson 1: What is Context and Why is it Critical?**

### Welcome!

Welcome to the first lesson. We're starting with the concept everything else in this course is built on. Get this one right and the rest of the course is elaboration; get it wrong and no amount of clever prompting will save your application.

### Learning Objectives

By the end of this lesson, you will be able to:
*   **Define** "context" and list the components that make it up in a modern system.
*   **Distinguish** context engineering from prompt engineering.
*   **Explain** why high-quality context is the primary lever on model behavior.
*   **Analyze** a failed AI interaction and identify the missing context.

---

### **1. Defining "Context": The AI's Worldview**

At its core, **context** is all the information an AI model uses to understand and respond to a request. Newcomers usually think context means "the question I typed." In reality it's a layered assembly of information that we, as engineers, deliberately construct.

Think of asking a human expert, "What's the status?" Their answer depends entirely on the situation:
*   In a hospital? A patient's status.
*   In a project meeting? A project update.
*   At a launch site? A rocket's status.

The expert uses their surroundings, the previous conversation, and their own experience to infer what you actually mean. **A model has none of that unless you supply it.** Whatever you put in the context window *is* the model's entire world for that turn.

> **Deep Dive: The Components of Context**
> In a modern system, context is assembled from:
> *   **System instructions:** the rules, persona, and constraints — the model's "job description."
> *   **The user's immediate request:** what was just asked.
> *   **Conversation history:** the preceding turns, providing short-term memory.
> *   **Retrieved information:** documents, database rows, or search results fetched at request time — the model's "reference library."
> *   **Tool definitions:** descriptions of the functions and services the model may invoke — its "abilities."
> *   **Tool results:** what came back when it used them — its "observations."
> *   **Examples:** demonstrations of the desired input/output shape — a "style guide."
> *   **Durable memory:** facts, preferences, and lessons persisted from earlier sessions.
> *   **Task state:** for agents, the current plan and how far along it is.
>
> The first five or six of these existed in 2023. The last three arrived with agents — and they're a large part of why this course keeps going after Module 3.

---

### **2. Context Engineering vs. Prompt Engineering**

These get used interchangeably, and the distinction is worth being precise about because it determines where you spend your effort.

**Prompt engineering** asks: *what words produce the behavior I want?* It's a discrete task — you write a good prompt, you're done, and it stays written.

**Context engineering** asks: *what configuration of information produces the behavior I want?* It's a continuous, runtime concern — a decision your code makes **on every single turn**, about what to include, what to leave out, what to compress, and in what order.

|  | Prompt engineering | Context engineering |
| :--- | :--- | :--- |
| **Unit** | The prompt | The whole context window |
| **When decided** | Once, at authoring time | Every turn, at runtime |
| **Who decides** | A human writing text | Code you wrote |
| **Typical failure** | Ambiguous instructions | Wrong, missing, or too much information |

Prompt engineering is a *subset* of context engineering — the system instructions are one component among many. You still need to write them well. But in a system that retrieves documents, calls tools, and runs for fifty turns, the words in your system prompt are a small fraction of what the model actually sees.

> **The one-sentence version:** prompt engineering is what you write; context engineering is what your code assembles.

---

### **3. The Amplified "Garbage In, Garbage Out" Principle**

"Garbage In, Garbage Out" is a classic idea. For language models it's amplified in a specific way: poor context doesn't produce an obviously broken answer. It produces a **fluent, confident, wrong** one — a hallucination. The failure is disguised as success, which makes it far more dangerous than a crash.

**Practical Example: The Vague Support Query**

A user is having trouble with their "Series A" smart fridge, and a support bot has access to all company documentation.

**Scenario A: Poor context**
The model gets only the raw question.
```json
{
  "user_query": "It's not working, what do I do?",
  "chat_history": []
}
```
**Response:**
> "I'm sorry to hear you're having trouble. Could you tell me what product you're using? You could try turning it off and on again, checking the power supply, or consulting the user manual."

Generic, unhelpful, and it pushes the work back onto the user.

**Scenario B: Engineered context**
```json
{
  "system_prompt": "You are a support assistant for ACME Inc. products. Use the provided information to help the user solve their problem. Prioritize solutions from the user's specific product manual.",
  "user_query": "It's not working, what do I do?",
  "chat_history": [
    { "user": "Hi, I need help with my new fridge.", "bot": "Of course! Can you tell me the model number?" },
    { "user": "It's the ACME SmartFridge Series A.", "bot": "Thank you. I have the Series A manual. What seems to be the issue?" }
  ],
  "retrieved_knowledge": [
    {
      "source": "manual_series_a.pdf",
      "content": "Common Issue: Ice maker not dispensing ice. Cause: The 'Child Lock' feature disables the ice and water dispenser. Solution: Press and hold the 'Lock' button for 3 seconds to deactivate. A green light indicates it's unlocked."
    }
  ]
}
```
**Response:**
> "I see you're using the ACME SmartFridge Series A. A common cause is the child lock being enabled, which disables the ice dispenser. Could you check whether there's a lock symbol on the display? If so, hold the 'Lock' button for three seconds."

Same model. Same question. The entire difference is the context we engineered.

---

### **4. Context as a Control Mechanism**

Context is the primary lever you have over model behavior — and it's a far more precise one than tone-of-voice tweaks to a prompt.

*   **Factual accuracy.** A model's internal knowledge is a frozen snapshot and can be wrong or outdated. Supplying facts in context grounds it in reality. Without that, it's pattern-matching against training data and hoping.

*   **Bias mitigation.** Models carry biases from their training data. Explicit rules in the context actively counteract them.

**Code Example: Mitigating Bias with Context**

Ask a model to write a job description with no guidance and you may get:
```
"...we are looking for a competitive code ninja... He will be responsible for..."
```
Gendered pronouns and exclusionary jargon. Now engineer the context:
```python
system_prompt = """
You are a hiring manager at a company committed to diversity and inclusion.
Write job descriptions that are welcoming to candidates of all genders,
backgrounds, and experience levels.

# RULES
1. Use gender-neutral language ('they', 'the candidate').
2. Avoid jargon that may exclude applicants ('code ninja', 'rockstar').
3. Focus on concrete skills and responsibilities.
4. Emphasize a collaborative, supportive environment.
"""
```
Result:
```
"...we are looking for a talented software developer to join our collaborative
team. The ideal candidate will be responsible for..."
```
Refining the instructions fundamentally changed the output. That's context engineering at its simplest.

---

### **5. A Preview of the Hard Part**

If context is this powerful, the obvious move is to include everything. That instinct is wrong, and understanding *why* is most of what this course teaches.

Context is a **finite, degrading resource**. It costs money and latency, and — less obviously — model accuracy falls as the window fills, well before any hard limit. Adding irrelevant information doesn't just waste tokens; it actively makes answers worse.

So context engineering is never "include more." It's a budgeting discipline: **the most useful information, in the fewest tokens, in the right order.** Module 4 gets rigorous about this. For now, just carry the instinct that more is not free.

---

### **Key Takeaways**

*   Context is **everything the model sees**, not just the user's question — instructions, history, retrieved data, tools, tool results, memory, and task state.
*   **Prompt engineering is what you write; context engineering is what your code assembles**, on every turn, at runtime.
*   Poor context produces **confidently wrong** answers, which is worse than obviously broken ones.
*   Context is your main control surface for accuracy, tone, and bias.
*   Context is **finite and degrades**. More is not better; better is better.

### **Hands-On Task: Deconstruct an AI Failure**

Think of a time an AI assistant gave you a bad or unhelpful answer.

1.  **Describe the situation.** What was your goal? What did you ask? What did it say?
2.  **Deconstruct the context, as the AI.**
    *   What was the **user query**?
    *   What do you think the **system instructions** were?
    *   What **knowledge** was missing? Was there a document it should have had?
    *   Was there **memory** it should have had from an earlier interaction?
3.  **Engineer a better context.**
    *   Rewrite the system instructions to be specific to your goal.
    *   Write the single piece of retrieved knowledge that would have unlocked a correct answer.
    *   Combine them into an improved context package.
4.  **Now find the failure it *didn't* have.** Name one piece of information that would have been *tempting* to include but would have made the answer worse. Why?

That last step is the habit that separates context engineering from "add more stuff."
