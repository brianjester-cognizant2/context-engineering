# **Module 3: Solutions to Hands-On Tasks**

This document provides the suggested solutions for the "Hands-On Tasks" in each lesson of Module 3.

---

### **[Lesson 1: Introduction to RAG](./Lesson1_Introduction_to_RAG.md)**

#### **Task: Design a RAG Prompt**

*Scenario: A retriever found a context chunk about PTO policy. You need to design the Generator prompt.*

#### **Example Solution:**

Here is a well-structured system prompt that combines the persona, rules, and the retrieved data:

```
# ROLE
You are a helpful and friendly HR assistant for ACME Inc. Your purpose is to answer employee questions accurately based on the official company handbook.

# RULES
1.  You MUST answer the user's QUESTION based ONLY on the provided CONTEXT.
2.  If the information to answer the question is not found in the CONTEXT, you MUST state: "I do not have enough information to answer that question from the employee handbook."
3.  You MUST cite the source of your information at the end of your answer.

# CONTEXT
---
**Source:** "employee_handbook.pdf", page 12
**Title:** "Time Off Policy"
**Content:** "Full-time employees receive 20 days of Paid Time Off (PTO) per year. PTO accrues at a rate of 1.67 days per month. Unused PTO can be rolled over, up to a maximum of 10 days. New employees start with a balance of 0 days and begin accruing PTO on their first day."
---

# QUESTION
How much vacation time do I get, and can I save it for next year if I don't use it?
```

---

### **[Lesson 2: Building and Managing the Knowledge Base](./Lesson2_Building_and_Managing_the_Knowledge_Base.md)**

#### **Task: The Chunking Challenge**

*Scenario: You are given a short document about the solar system and asked to analyze different chunking strategies.*

#### **Example Solution:**

1.  **Manual Chunking:**
    *   **Reasoning:** The most logical splits are between the distinct topics. The first topic is the inner planets, and the second is the gas giants. A further split between each planet makes sense as each is a self-contained idea.
    *   **Implementation:**
        ```
        The Solar System has 8 planets. Mercury is closest to the Sun. It is very hot.
        ---
        Venus is the second planet. It has a thick atmosphere.
        ---
        Earth is the third planet. It is our home.
        ---
        The Gas Giants are Jupiter, Saturn, Uranus, and Neptune.
        Jupiter is the largest planet. It has a Great Red Spot.
        ---
        Saturn is known for its beautiful rings.
        ```

2.  **Fixed-Size Chunking (`chunk_size=70`):**
    *   **First Chunk:** `The Solar System has 8 planets. Mercury is closest to the Sun. It is ve`
    *   **Problem:** This method is blind to the meaning and structure of the text. It unnaturally splits the sentence "It is very hot," losing the semantic relationship and making the chunk less useful for answering questions about Mercury.

3.  **Recursive Chunking (on `\n\n`):**
    *   **First Chunk:** `The Solar System has 8 planets. Mercury is closest to the Sun. It is very hot.\nVenus is the second planet. It has a thick atmosphere.\nEarth is the third planet. It is our home.`
    *   **Second Chunk:** `The Gas Giants are Jupiter, Saturn, Uranus, and Neptune.\nJupiter is the largest planet. It has a Great Red Spot.\nSaturn is known for its beautiful rings.`
    *   **Why it's better:** By splitting on the double newline, the recursive chunker correctly identifies the paragraphs as the primary semantic boundary. It keeps all the inner planets in one chunk and all the gas giants in another, preserving the logical grouping of the original document.

4.  **Find the orphan:**
    *   The answer lives in the **second chunk**: *"The Gas Giants are Jupiter, Saturn, Uranus, and Neptune."*
    *   **Would a semantic search for "How many planets are gas giants?" retrieve it?** Probably — this chunk happens to be lucky, because it literally contains the phrase "Gas Giants." But notice what it *doesn't* contain: the words **"Solar System"** and **"planets"** as a count. Those are in the first chunk. If the corpus contained material about gas giants in *other* star systems, or about Jupiter's moons, this chunk has nothing to distinguish itself as being about *our* solar system.
    *   **What's missing** is the document-level frame. The chunk is true but unanchored — it doesn't know what document it came from or what question it answers.

5.  **Contextualize it:**
    > *"This chunk is from an introductory overview of the Solar System's eight planets, in the section describing the outer planets. The Gas Giants are Jupiter, Saturn, Uranus, and Neptune. Jupiter is the largest planet..."*
    *   **The words doing the retrieval work** are **"Solar System"**, **"eight planets"**, and **"outer planets."** None of them appear in the original chunk.
    *   **Why they weren't there already:** they were in the document's opening sentence and its implicit structure — information a human reader carries forward while reading, and which chunking discards. Contextual retrieval is, precisely, the act of restoring what the reader would have remembered.


---

### **[Lesson 3: The Retrieval Process](./Lesson3_The_Retrieval_Process.md)**

#### **Task: Choose Your Retrieval Strategy**

#### **Example Solution:**

1.  **Scenario A: "What is context engineering?"** → **MMR, over a hybrid base.**
    A broad definitional query is exactly where standard similarity search returns five near-identical introductory paragraphs. MMR penalizes each result for resembling the ones already chosen, producing coverage rather than repetition — which is what a definitional answer needs.

2.  **Scenario B: "error code G-451"** → **Hybrid search.**
    "G-451" carries no semantic content for an embedding model to represent. Pure vector search will happily return thematically related troubleshooting prose that never mentions the code. The BM25 half guarantees the exact match; the vector half supplies surrounding context if no exact match exists.

3.  **Scenario C: "How do I add a user to my account?"** → **Standard vector search is sufficient** (hybrid costs nothing extra and is still fine).
    A direct query whose answer sits in one specific how-to document. Redundancy isn't a risk, so MMR's diversity has nothing to buy. This is the case where the simple option is genuinely the right one.

4.  **Scenario D: invoices over $10,000 from Q2, still unpaid** → **Not retrieval at all. Write a SQL query.**
    Every clause of that request maps to a structured field with an exact comparison: `amount > 10000 AND quarter = 'Q2' AND status = 'unpaid'`. Embedding 400,000 invoice records to approximately answer a question SQL answers exactly is the most common expensive mistake in applied RAG. Semantic similarity is for when you *can't* express the query precisely — here you can.

5.  **Defending the default.**
    Hybrid search would have been acceptable for all of A, B, and C. It costs one extra keyword query and a fusion step, and it never does worse than pure vector search — the failure it prevents (missed exact tokens) has no corresponding failure it introduces.

    The scenario where **pure vector search is materially worse is B**, and the mechanism is worth stating precisely: an embedding model maps text to a point representing *meaning*. "G-451" has no meaning in the training distribution — it's an arbitrary token — so its embedding is essentially noise, positioned near other short alphanumeric strings rather than near the document that documents it. The retrieval doesn't just perform worse; it performs *arbitrarily*, and it returns confident, plausible, wrong results.

---

### **[Lesson 4: The Generation and Synthesis Process](./Lesson4_The_Generation_and_Synthesis_Process.md)**

#### **Task: Critique a Generated Answer**

*Scenario: A RAG system answers "When did the Roman Empire fall?"*

#### **Example Solution:**

1.  **Is it factually correct?**
    *   Yes, the answer "The Roman Empire fell in 476 AD after Romulus Augustulus was deposed" is factually correct based on the provided context.

2.  **Is it complete?**
    *   No, it is incomplete. It omits the crucial detail that this event is traditionally seen as the end of the **Western** Roman Empire, and it fails to mention the key figure of **Odoacer**, the Germanic chieftain who deposed the emperor.

3.  **Is it trustworthy?**
    *   No, it is not fully trustworthy because it is **missing the citation**. The user has no way of knowing where the information came from.

4.  **Rewrite the Generated Answer:**
    *   A much better answer would be: "According to the provided text, the traditional date for the fall of the **Western** Roman Empire is 476 AD, which is when the last emperor, Romulus Augustulus, was deposed by the Germanic chieftain Odoacer (Source: history_ch4.pdf)." 
---

### **[Lesson 5: Agentic Retrieval and the Limits of Vector RAG](./Lesson5_Agentic_Retrieval.md)**

#### **Task: Choose and Combine**

#### **Example Solution — Part A:**

1.  **80,000 Zendesk tickets → Vector RAG (hybrid).**
    Large corpus of unstructured natural-language prose where the user's phrasing will rarely match the ticket's phrasing ("payment failed" vs. "card declined at checkout"). The deciding property is that **relationships between tickets are implicit** — there is no link structure to traverse — which is precisely where semantic similarity earns its keep.

2.  **2M-line monorepo → Agentic search.**
    Every property from section 2 applies: exact identifiers, an explicit import/call graph, chunking that mutilates functions, and an index that goes stale between commits. The deciding property is **traversability** — most real code questions are "what calls this and what does it assume," which is a graph walk, not a similarity query.

3.  **Churn and MRR over a data warehouse → Direct query.**
    Structured data with exact fields. Not a retrieval problem at all; it's a `GROUP BY`. The agent's job is to write correct SQL, not to find similar rows. Give it the schema and a query tool.

4.  **30-page handbook → None. Just include it.**
    Thirty pages is roughly 20–25k tokens, which fits comfortably in a modern window and caches perfectly as a stable prefix. Building an index for it is infrastructure that adds staleness, a sync job, and a failure mode, in exchange for saving tokens you can afford. **Retrieval is a response to scale you don't have here.**

5.  **Production incident debugging → Both, plus direct query.**
    Genuinely mixed: logs and traces are semi-structured with exact identifiers (trace IDs, error codes) and want keyword/agentic search; deploy history is structured and wants a query; past postmortems are prose and want vector RAG. See Part B.

6.  **15 years of contracts, "unusual liability caps" → Vector RAG (hybrid), with a caveat.**
    Prose corpus, fuzzy semantic query, implicit relationships — textbook vector RAG. The caveat is that *"unusual"* is a comparative judgment retrieval cannot make: you must retrieve all liability-cap clauses (high recall, using hybrid search plus a clause-type filter) and then have the model compare them. This is a case where **the retrieval target is a category, not an answer** — design for recall and let the reasoning happen downstream.

#### **Example Solution — Part B: the incident router**

```python
def investigate_incident(incident_id):
    # 1. STRUCTURED FIRST — cheap, exact, and it bounds everything downstream.
    inc     = db.get_incident(incident_id)            # start/end time, services
    deploys = db.deploys_in_window(inc.window, inc.services)

    # 2. EXACT-IDENTIFIER SEARCH — logs and traces keyed by what we now know.
    errors  = log_search(services=inc.services, window=inc.window, level="ERROR")
    traces  = trace_search(trace_ids=[e.trace_id for e in errors[:20]])

    # 3. AGENTIC EXPLORATION — only if the above didn't localize the fault.
    if not localized(errors, traces):
        hypothesis = agent_explore(
            question=f"What in {inc.services} could produce {top_error(errors)}?",
            tools=[grep_logs, read_code, git_blame, read_config],
            budget=40_000,
        )
    else:
        hypothesis = from_evidence(errors, traces, deploys)

    # 4. SEMANTIC RAG LAST — "have we seen this before?" is a fuzzy question.
    priors = vector_search(describe(hypothesis), corpus="postmortems", k=3)

    return Report(timeline=..., hypothesis=hypothesis, priors=priors)
```

**Order and escalation:** structured query → exact-identifier search → agentic exploration → semantic RAG. The first two are cheap, deterministic, and *narrow the search space* for everything after them. The escalation condition into step 3 is `not localized(...)` — the exact searches found errors but couldn't tie them to a cause. Semantic RAG comes **last** deliberately: "have we seen this before" is only answerable once you know what *this* is, and running it first would retrieve postmortems matching the incident's superficial description rather than its actual mechanism.

#### **Example Solution — Part C: costing the reversal**

**1. The costs**
*   **Vector RAG:** $400/month infrastructure. (Plus embedding costs for the nightly re-index, and engineer time maintaining the pipeline — neither of which is in the stated figure, which is itself worth noting.)
*   **Agentic search:** 2,000 queries × 25,000 tokens = 50M tokens/month × $5/1M = **$250/month.**

Agentic search is **cheaper** at this volume, which inverts the premise of the question. That's the first lesson: *run the numbers before accepting a framing.* The naive assumption that "more tokens" means "more expensive" ignores that the vector pipeline has a fixed cost floor that 2,000 queries/month doesn't come close to amortizing.

**2. The strongest argument for switching, even if it were more expensive**

**It eliminates silent staleness.** A nightly re-index means that for up to 24 hours the agent answers questions about code that no longer exists — and it answers them *confidently*, because a retrieved chunk carries no signal that it's out of date. On a monorepo with many merges a day, this isn't an edge case; it's the normal state of the index for most of the working day. The failure is invisible in traces (retrieval succeeded, the model answered), invisible in evals (which run against a fixed snapshot), and surfaces as an engineer wasting an hour on advice about a deleted function.

Agentic search cannot have this failure. `grep` reads the working tree. The result is either current or absent.

**3. The measurement to take first**

**Retrieval quality on a held-out set of real questions** — specifically, context recall (Module 6, Lesson 1): for 50 actual questions engineers asked, does each approach surface the file that genuinely contains the answer?

*What would change the recommendation:* if agentic search's recall is **worse** — plausible if your codebase has poor naming, so that keyword guesses miss — then you're paying more for less, and the right move is neither/both: keep the vector index as a *fallback* for when grep comes up empty, and route by whether the query contains an extractable identifier.

The general principle: **measure the thing you're actually trading (accuracy), not the thing that's easy to measure (cost).**
