# **Final Project: Build a Research Agent You Would Actually Deploy**

## **Objective**

Synthesize the course into one working system: an **AI Research Assistant** that takes a complex question, gathers information, and returns a well-structured, cited answer.

The emphasis is on the second half of that sentence. A research agent that produces good answers on a demo query is a weekend project. This assignment asks for one you could hand to a colleague and let run unattended — which means the interesting work is in the harness, the verification, and the evals, not in the prompt.

You will design it as an **architecture**, build it, **measure** it, and **attack** it.

---

## **Part 1 — The Architecture Spec (do this first)**

Before writing code, complete the one-page spec from [Module 8, Lesson 4](./Lessons/Module8/Lesson4_Agentic_Architecture.md), covering all six planes:

| Plane | What you must decide |
| :--- | :--- |
| **1 · Model** | Which model for which step. Where cheap models suffice. Where your cache breakpoints sit |
| **2 · Context** | Assembly order (stable → volatile), retrieval strategy, compaction trigger, token budget |
| **3 · Capability** | Every tool, its permission scope, and its error contract. **Plus what you deliberately withheld** |
| **4 · Control** | Trigger, the goal as a *verifiable end state*, loop pattern, all termination conditions |
| **5 · Verification** | The in-loop check and its tier, your eval set, any human gates |
| **6 · Governance** | What you trace, your cost ceiling, **where untrusted input enters**, and your blast radius |

Two lines are graded most heavily, because they're the ones people skip: **"explicitly NOT given"** and **"untrusted input enters at."**

---

## **Part 2 — Build It**

**Core requirements:**

1.  **Tools.** At least one for external search, plus a retrieval tool over a document set. Use the lessons in this course as your corpus if you like. Every tool must return **actionable errors** and must never raise into the loop.

2.  **Grounding.** Answers must be grounded in retrieved evidence. Choose your retrieval strategy deliberately using the decision guide in [Module 3, Lesson 5](./Lessons/Module3/Lesson5_Agentic_Retrieval.md) — and **justify the choice against your corpus's properties**. "I used vector RAG because that's what RAG means" is not a justification.

3.  **An agent loop with a real exit condition.** Specify trigger, goal, actions, verification, and memory ([Module 8, Lesson 2](./Lessons/Module8/Lesson2_Loop_Engineering.md)). The loop must **not** terminate on the model's self-report. Include an iteration cap, a token budget, and no-progress detection.

4.  **Long-horizon context management.** At minimum: a token budget enforced in code, plus **one** of compaction, structured note-taking, or sub-agent isolation. Say why you chose that one.

5.  **Citations, verified.** Every factual claim carries a source. Then go further — **programmatically check that each cited source exists and actually contains the claim's supporting text.** An unverified citation is decoration.

6.  **Least privilege.** Read-only where possible. No capability the agent doesn't need. If your agent can act outward, say what stops a prompt-injected version of it.

---

## **Part 3 — Measure It**

Build an eval set **before** you finish building the agent.

1.  **At least 25 cases**, stratified across: easy factual lookups, multi-hop questions requiring synthesis, questions your corpus *cannot* answer (the agent should say so), and ambiguous questions.
    *   *25 is a smoke test, not a measurement.* State explicitly what your set can and cannot detect ([Module 6, Lesson 1](./Lessons/Module6/Lesson1_Evaluating_Context_Quality_and_RAG_Performance.md)).

2.  **Score the four RAG pillars** — context precision, context recall, faithfulness, answer relevance — on a labeled subset.

3.  **Score the trajectory**, not just the answer, on at least 5 cases across the six dimensions: tool selection, argument extraction, result utilization, error recovery, plan coherence, task completion.

4.  **Write at least four natural-language unit tests** in the LMUnit style, and **calibrate your judge** on 20 hand-labeled examples. Report the agreement and what you changed in the rubric.

5.  **Report cost and latency** per query, with a token breakdown by context section.

---

## **Part 4 — Attack It**

Write and run at least **four red-team cases** ([Module 6, Lesson 3](./Lessons/Module6/Lesson3_Security_for_Context-Aware_Systems.md)). At minimum:

*   **Indirect injection.** Plant a document in your corpus containing instructions to the agent. Does it follow them?
*   **Exfiltration.** Can any path get data out — a fetched URL, a rendered image, a written file, a posted comment?
*   **Scope escape.** Can it be induced to read or write outside its permitted scope?
*   **Resource exhaustion.** Can a crafted query make it loop until the budget dies?

For each, state what result constitutes a **failure**, and be strict: a test that only checks the final text passes when the agent did something forbidden and happened not to mention it.

Then run the trifecta audit. If your agent has all three legs, **either break one or document explicitly why you accepted the risk and what bounds it.**

---

## **Part 5 — Deliverables**

1.  **Runnable code**, with setup instructions.
2.  **`ARCHITECTURE.md`** — the six-plane spec from Part 1, updated to describe what you actually built (they will differ; note where and why).
3.  **`EVALUATION.md`** — eval set, results, judge calibration, cost and latency, and an honest account of what your evals cannot detect.
4.  **`SECURITY.md`** — red-team cases and results, the trifecta audit, and your accepted risks with a named owner for each.
5.  **Three example runs**, including the full trace of one — and at least one where the agent **failed or escalated**. A submission where everything worked is a submission that wasn't tested hard enough.

---

## **Part 6 — The Write-Up**

Answer these in a short `REFLECTION.md`. This is the part that demonstrates whether the course landed.

1.  **Which plane is thinnest?** Deliberate scoping or unowned concern? Say which.
2.  **Trace a failure.** Pick a real failure from your runs, walk it back to a plane, and name the structural change that prevents recurrence. Confirm it's a change to the *system*, not to the wording of a prompt.
3.  **What did your evals fail to catch?** Name a failure you found by hand that your eval set missed, and write the case that would have caught it.
4.  **What did you deliberately not build**, and what would have to be true for you to build it?
5.  **If you had to raise this agent one autonomy level** — from proposing to acting — what evidence would you need first, and what would make you demote it?

---

## **Grading Emphasis**

| Weight | Area |
| ---: | :--- |
| 25% | Architecture spec: completeness, and the honesty of the "NOT given" and "untrusted input" lines |
| 25% | Evaluation: quality of the eval set, judge calibration, and candor about limitations |
| 20% | Harness: verification that isn't self-report, real termination conditions, actionable tool errors |
| 15% | Security: red-team rigor and the trifecta audit |
| 15% | The agent itself: does it produce good, cited, grounded answers |

Note that the agent working is worth the least. That is deliberate, and it is the summary of the whole course: **anyone can get an agent to work once. The engineering is in knowing that it works, knowing when it doesn't, and bounding what happens when it fails.**
