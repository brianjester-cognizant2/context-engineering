# **Module 1: Solutions to Hands-On Tasks**

This document provides suggested solutions for the "Hands-On Tasks" in each lesson of Module 1.

---

### **[Lesson 1: What is Context and Why is it Critical?](./Lesson1_What_is_Context.md)**

#### **Task: Deconstruct an AI Failure**

#### **Example Solution:**

**1. The situation**
*   **Goal:** the hours for the downtown branch of my bank on an upcoming public holiday.
*   **Question:** "What are your hours for the downtown branch on Monday?"
*   **Answer:** "Our general branch hours are 9 AM to 5 PM, Monday to Friday. Hours may differ on public holidays. For accurate information, please visit our website."

**2. Deconstructing the context**
*   **User query:** as above.
*   **Inferred system instructions:** *"You are a helpful assistant for XYZ Bank. Answer politely. If you don't know, give general information and direct the user to the website."* — note that the last clause actively *causes* the bad answer. It gives the model a comfortable exit that looks like helpfulness.
*   **Missing knowledge:** (a) branch-specific hours, (b) a holiday calendar with per-branch exceptions.
*   **Missing memory:** which branch is "mine." I'd told the app this before; the assistant had no access to it.

**3. An engineered context**

Improved instructions:
```
You are a banking assistant for XYZ Bank. Answer using the real-time branch data
in context. If the specific data needed is not present, say exactly what you are
missing — do not substitute general information for a specific answer.
```
The key change is the last clause: the old prompt rewarded generic deflection, the new one forbids it.

Required knowledge:
```json
{
  "retrieved_knowledge": [{
    "source": "branch_hours.db",
    "branch_name": "Downtown Branch",
    "regular_hours": { "monday": "9 AM - 5 PM", "tuesday": "9 AM - 5 PM" },
    "holiday_exceptions": [
      { "date": "2026-10-12", "holiday": "Thanksgiving Day", "hours": "Closed" }
    ]
  }],
  "user_memory": { "preferred_branch": "Downtown Branch" }
}
```
Result: *"The downtown branch is closed on Monday, October 12th, for Thanksgiving Day. It reopens Tuesday at 9 AM."*

**4. What *not* to include**

The complete list of all 340 branches and their hours. It is *relevant-looking* — it certainly contains the answer — but at tens of thousands of tokens it buries the two lines that matter in the low-attention middle of the window, costs 50× more, and measurably raises the odds the model reports the wrong branch's hours. Retrieval exists precisely so that "the data contains the answer" and "the data is in the context window" stay different things.

---

### **[Lesson 2: The Evolution and Economics of Context](./Lesson2_Evolution_and_Economics.md)**

#### **Task: The Napkin-Math of an Agent**

#### **Example Solution:**

**1. One conversation, no caching**

Input tokens per turn = 2,000 (stable) + 1,500 (docs) + accumulated history.

| Turn | Stable | Docs | History | Input |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 2,000 | 1,500 | 0 | 3,500 |
| 2 | 2,000 | 1,500 | 400 | 3,900 |
| 3 | 2,000 | 1,500 | 800 | 4,300 |
| 4 | 2,000 | 1,500 | 1,200 | 4,700 |
| 5 | 2,000 | 1,500 | 1,600 | 5,100 |
| 6 | 2,000 | 1,500 | 2,000 | 5,500 |
| 7 | 2,000 | 1,500 | 2,400 | 5,900 |
| 8 | 2,000 | 1,500 | 2,800 | 6,300 |
| | | | **Total** | **39,200** |

*   Input: 39,200 / 1M × $5.00 = **$0.1960**
*   Output: 8 × 150 = 1,200 tokens → 1,200 / 1M × $25.00 = **$0.0300**
*   **Total: $0.2260 per conversation**

**2. With caching**

The 2,000-token stable prefix is written once (turn 1) and read on turns 2–8.

*   Cache write, turn 1: 2,000 / 1M × $5.00 × 1.25 = **$0.0125**
*   Cache reads, turns 2–8: 7 × 2,000 = 14,000 → 14,000 / 1M × $0.50 = **$0.0070**
*   Uncached input (docs + history, all turns): 39,200 − 16,000 = 23,200 → 23,200 / 1M × $5.00 = **$0.1160**
*   Output: **$0.0300**
*   **Total: $0.1655 per conversation**

**3. The saving**

$0.2260 − $0.1655 = **$0.0605**, a **27% reduction**.

Probably smaller than expected — the headline "90% off cached tokens" is real, but it only applies to the 41% of input that *is* the stable prefix. **Caching saves a large fraction of a modest share of your bill.** The lesson generalizes: work out what proportion of your context is genuinely stable before you predict the win.

**4. At scale**

5,000 conversations/day × 30 days = 150,000 conversations.
*   Uncached: 150,000 × $0.2260 = **$33,900/month**
*   Cached: 150,000 × $0.1655 = **$24,825/month**
*   **Difference: ~$9,075/month** for a change that is an ordering decision plus a cache-control parameter.

**5. Adding routing**

Three of eight turns move to the small model ($0.25/$1.25 per 1M). Take turns 3, 5, and 7 (inputs 4,300 / 5,100 / 5,900 = 15,300 tokens; outputs 450).

*   Small-model cost: 15,300 / 1M × $0.25 + 450 / 1M × $1.25 = $0.0038 + $0.0006 = **$0.0044**
*   Remaining five turns on the frontier model, with caching: stable prefix write $0.0125 + 4 reads (8,000 tokens) $0.0040 + uncached input (3,500+3,900+4,700+5,500+6,300 = 23,900, less 5×2,000 stable = 13,900) → 13,900 / 1M × $5.00 = $0.0695 + output (5 × 150 = 750) $0.0188
*   **Total ≈ $0.1092** — a further ~34% off the cached figure, and **52% below** the naive baseline.

**Which lever mattered more?** Routing, here — and by a wider margin than caching. At 40 turns the ranking would likely **flip**: history grows to dominate input, and the stable prefix's share shrinks, so caching's percentage win falls further while routing's win grows with the number of routable turns. The general rule: **caching wins when your context is mostly stable; routing wins when your turns are mostly easy.** Measure the mix before choosing where to spend a week.

**6. The timestamp bug**

Putting `"Current time: {timestamp}"` as the *first line* changes byte 1 of the prompt on every call. The cache prefix is valid only up to the first changed byte, so **nothing caches, ever**. Cost returns to the full $0.2260 — a 37% increase — with no error, no warning, and no behavioral change.

**How you'd notice:** the cache-read token counts in the API response drop to zero. Alert on cache hit rate as a first-class metric; it's the only visible symptom.

**Where it should go:** at the *bottom*, adjacent to the current request, in the volatile zone. Better still, don't put it in the prompt at all — expose a `get_current_time()` tool, so the model gets it only when it actually needs it, and the whole prefix stays stable.

---

### **[Lesson 3: Core Principles of Effective Context Design](./Lesson3_Core_Principles.md)**

#### **Task: Altitude Calibration**

#### **Example Solution — Part A: the classifier prompt**

```
# ROLE
You are an email classification agent. Your only job is to route incoming
support email to the correct department.

# INSTRUCTIONS
Classify the email into exactly ONE category:

1. [Billing] — invoices, payments, subscriptions, refunds, pricing.
2. [Technical Support] — product functionality, errors, bugs, installation,
   how-to questions.
3. [General Inquiry] — everything else: partnerships, feature requests,
   press, and anything that fits none of the above.

# RULES
- If an email spans two categories, choose the one the sender most wants
  resolved.
- Never invent a fourth category.

# OUTPUT FORMAT
Return ONLY the category tag. No explanation, no punctuation, no preamble.

# EXAMPLE
Email: "Hi, I can't log in to my account."
Output: [Technical Support]
```

The tie-break rule is doing real work: multi-topic emails are the majority of real misclassifications, and without a rule the model picks arbitrarily and inconsistently.

#### **Example Solution — Part B: fixing the altitude**

**1. Clause-by-clause**

| Clause | Altitude | Why |
| :--- | :--- | :--- |
| "Be helpful" | **Too high** | Says nothing actionable |
| "If angry, be extra polite" | About right | A genuine behavioral heuristic |
| The entire refund matrix | **Far too low** | Business policy hardcoded in a prompt — brittle, unversioned, and stale the moment policy changes |
| The shipping matrix | **Far too low** | Same problem; also *data*, not instruction |
| "Don't disparage competitors" | About right | A real constraint, briefly stated |
| "Manager will call within 24 hours" | **Too low** | A promise hardcoded with no ability to check whether it's true |
| "If confused, explain simply" | About right | Reasonable heuristic |
| "If profanity, stay professional" | About right | Reasonable constraint |
| "Never promise what you can't deliver" | About right | Good general guardrail |
| "Use good judgment" | **Too high** | Filler |

**2. The rewrite**

```
# ROLE
You are a customer service agent for <Company>.

# SOURCE OF TRUTH
Refund, shipping, and membership rules are provided in the RETRIEVED POLICY
section of your context. State a rule ONLY if it appears there. If the
retrieved policy does not cover the situation, say so and escalate — never
infer a policy.

# TOOLS
- `check_order(order_id)` for order status, dates, and membership tier.
- `request_callback(reason)` to schedule a manager callback. Use the time
  the tool returns; never state a callback window yourself.

# CONDUCT
- Match the customer's urgency; stay professional regardless of their tone.
- Explain simply when the customer seems confused.
- Do not comment on competitors.
- Never promise an outcome you have not confirmed with a tool.
```

**What moved where, and why:**
*   **Refund and shipping matrices → retrieved knowledge.** They are versioned business policy that changes without an engineer being involved. In the prompt they are invisible to the policy team, unversioned, untestable, and stale by default.
*   **Membership tier and order dates → a tool call.** These are per-customer *facts*. A prompt cannot know them; asking the model to reason about "if they're a Premium member" without a way to check is asking it to guess.
*   **The callback window → a tool return value.** "24 hours" was a hardcoded promise nobody could verify. Now it reflects reality.

**3. What breaks if the refund matrix stays**

The rules will change — a new membership tier, a regional variation, a regulatory requirement — and the change will be made by someone in Finance or Legal who has no idea a copy lives in a prompt in a repository. The agent then confidently quotes retired policy to customers, indefinitely, and nothing in your test suite fails because the prompt still says exactly what it always said.

That's the general form of the altitude failure: **putting data in the prompt makes it invisible to the people who own it.** As the business grows, the matrix also grows — every exception adds a clause until the prompt is three pages, nobody can safely edit it, and the model's attention is spread across dozens of conditions of which one is relevant.

---

### **[Lesson 4: The Four Disciplines](./Lesson4_The_Four_Disciplines.md)**

#### **Task: Diagnose the Discipline**

#### **Example Solution:**

| # | Symptom | Discipline | Fix | The wrong fix people reach for |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Inconsistent bullets vs. prose | **Prompt** | Specify the format explicitly; add one canonical example | Switching to a bigger model |
| 2 | Degrades after 30 minutes | **Context** | Compaction; restate the task at the end of the window | Raising the temperature, or blaming the model |
| 3 | Quotes retired policy | **Context** | Fix the index — the old document is still retrievable. Add recency filtering and citations | Adding "use only current policy" to the prompt, which the model cannot act on because it can't tell which is current |
| 4 | "All tests pass," never ran | **Harness** | Verification gates termination; the test runner decides, not the model | "ALWAYS verify before claiming completion" in the prompt |
| 5 | Works by hand, fails unattended | **Loop** | Real trigger, verifiable goal, retries, escalation on failure | Re-running it manually and concluding it works |
| 6 | Wrong tool among fifteen | **Context** (tool descriptions are context) | Prune overlapping tools; make descriptions disjoint and specific about *when* to use each | Adding "use search_tickets for ticket questions" to the prompt — treating a fifteen-way ambiguity one clause at a time |
| 7 | 8× bill, prefix billed in full | **Context + Harness** | Find the volatile token above the prefix; reorder stable → volatile; add cache-hit-rate monitoring and a budget cap | Shortening the system prompt — which addresses 12% of the waste and none of the cause |

**Two prompt "fixes" that won't hold:**

*   **#4:** *"ALWAYS run the tests and verify they pass before claiming the task is complete."* This fails because it asks a model to reliably choose the less satisfying completion, on every run, forever, under context pressure. It will work most of the time — which is worse than failing consistently, because the failures become rare enough to stop expecting and are always discovered downstream.

*   **#3:** *"Only use current policy documents; ignore outdated ones."* This fails because the model has **no way to tell which is current.** Both documents are in its context, both look authoritative, and neither is labeled. The instruction asks for a judgment the model has no information to make. The fix has to happen at retrieval time, where the metadata exists.
