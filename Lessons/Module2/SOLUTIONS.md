# **Module 2: Solutions to Hands-On Tasks**

This document provides suggested solutions for the "Hands-On Tasks" in each lesson of Module 2.

---

### **[Lesson 1: The Anatomy of an Advanced Prompt](./Lesson1_Anatomy_of_an_Advanced_Prompt.md)**

#### **Task: Design a Meeting Summarizer**

#### **Example Solution — Part A: the system prompt**

```
# ROLE
You are a meticulous chief of staff. You produce meeting summaries that someone
who missed the meeting can act on without asking follow-up questions.

# PROCESS
Work through the transcript in this order:
1. Identify the distinct topics discussed.
2. Extract decisions that were actually made — a conclusion someone committed to,
   not a possibility that was raised.
3. Extract action items: what will be done, by whom, and by when.

# RULES
- Report only what is in the transcript. Do not infer decisions from discussion.
- If an action item has no clear owner, list it under Action Items with the owner
  as **UNASSIGNED** and quote the sentence it came from. Never guess an owner.
- If a decision was discussed but explicitly deferred, place it under Key
  Decisions marked **DEFERRED**, with what it is blocked on.
- Preserve exact figures, dates, and names as spoken.

# OUTPUT FORMAT
## Summary
2–4 sentences covering what the meeting was about and where it landed.

## Key Decisions
- **<decision>** — <one line of rationale, if stated>

## Action Items
- **<owner>** — <action> — <due date, or "no date given">
```

The `UNASSIGNED` rule is the important part of this prompt. The two natural failure modes are inventing an owner (the model picks whoever spoke last) and silently dropping the item. An explicit third option — surface it, flag it, quote the source — is what makes the output trustworthy, because the reader can see exactly what needs a human decision.

#### **Example Solution — Part B: what belongs where**

| Suggestion | Verdict | Where it goes |
| :--- | :--- | :--- |
| "Sarah is VP Engineering, Marcus runs Product, Priya leads Design" | **Doesn't belong** | A retrieved roster, or a tool. It's per-company data that changes with every hire and departure; in the prompt it's invisible to HR and stale by default. It also doesn't scale — this works for 3 people and fails at 300 |
| "Never include anything after 'off the record'" | **Belongs** | A processing rule that applies to every transcript, stable over time, and checkable |
| "We say 'workstream', not 'project'" | **Belongs** | House style — stable, short, genuinely instruction |
| "Transcript is from {date} in {room}" | **Doesn't belong in the system prompt** | It's volatile per-request data. Put it with the transcript in the user turn, at the bottom of the context. In the system prompt it would invalidate the cache prefix on every single call (Module 1, Lesson 2) |

#### **Example Solution — Part C: negatives to positives**

| Negative | Positive rewrite |
| :--- | :--- |
| "Do not infer decisions from discussion." | "Record a decision only when a participant states a commitment. Discussion of options is not a decision." |
| "Never guess an owner." | "Assign an owner only when the transcript names one. Otherwise mark **UNASSIGNED** and quote the source sentence." |
| "Don't include filler or small talk." | "Include only content relating to the meeting's topics, decisions, and actions." |

Each rewrite gives the model a **test it can apply** rather than a category to avoid. "Don't include filler" requires the model to define filler; "include only content relating to topics, decisions, and actions" gives it three concrete buckets and everything else falls out.

---

### **[Lesson 2: Foundational Prompting Techniques](./Lesson2_Foundational_Prompting_Techniques.md)**

#### **Task: From Zero to Few-Shot**

#### **Example Solution:**

**Part A — escalating**

*1. Zero-shot.* System prompt: *"Explain what the given code does in one simple English sentence."* On `def add(a, b): return a + b`, across three runs you'll typically see variation like:
*   "This function adds two numbers together and returns the result."
*   "The `add` function takes two arguments, `a` and `b`, and returns their sum."
*   "This is a simple addition function that returns a + b."

All correct. None identical in voice, tense, or whether they name the function. If you're rendering these in a UI or diffing them, that's a problem.

*2. One-shot.*
```
User:      def multiply(x, y): return x * y
Assistant: Returns the product of its two arguments.
```
The format collapses onto that shape immediately: terse, third person, no function name, no preamble. **What specifically changed** is not comprehension — it's that the model now has a concrete target for *register and length*, which is exactly what no amount of adjectives in the system prompt reliably conveys.

*3. Few-shot.*
```
User:      def multiply(x, y): return x * y
Assistant: Returns the product of its two arguments.

User:      squares = [x*x for x in range(10)]
Assistant: Builds a list of the squares of the integers 0 through 9.

User:      @lru_cache(maxsize=None)
           def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)
Assistant: Computes Fibonacci numbers recursively, caching results so each value
           is calculated only once.
```
The third example teaches that a decorator's *effect* is part of the explanation — otherwise the model describes the recursion and ignores the memoization entirely.

**Part B — breaking it**

Given a 40-line class with three methods, the prompt will still return one sentence, and that sentence will be something like *"Defines a class for managing user sessions."* Technically true, practically useless — it says nothing about the invariant, the methods, or the lifecycle.

**The examples capped the output.** Every demonstration was a one-liner explaining a single expression, so the model learned "one clause, regardless of input complexity." This is the section-5 failure mode exactly: examples don't just guide, they bound. The fix is either an example showing a multi-line explanation for a complex input, or an explicit length rule scaled to input complexity — *"one sentence for a single function; up to four for a class, one per public method."*

**Part C — the boundary example**

```
User:      def save_report(data):
               total = sum(data)
               db.execute("INSERT INTO reports VALUES (?)", total)
               return total
Assistant: Sums the input values, writes the total to the reports table, and
           returns it.
```

**Why this is the right example rather than just an example:** it isolates the single variable in question. The function is otherwise trivial — the computation is a `sum`, which the model already handles — so the only thing the example teaches is *side effects are part of what the code does*. The clause structure ("sums…, writes…, and returns…") also demonstrates the pattern the model should reuse. An example that was complex in several ways at once would teach several things weakly instead of one thing strongly.

---

### **[Lesson 3: Advanced Prompting Strategies](./Lesson3_Advanced_Prompting_Strategies.md)**

#### **Task: The Multi-Step Meal Planner**

#### **Example Solution — Part A: the chain**

**1. Generate.**
```
You are a registered dietitian. Produce a 3-day meal plan.

# CONSTRAINTS (all are hard)
- Low-carb: under 50g net carbs per day.
- No fish or shellfish, including sauces and stocks containing them.
- 3 meals per day, 3 days.
- Nutritionally complete: adequate protein, fibre, and micronutrients.
- No single protein source appears more than twice across the nine meals.

For each meal give: name, main protein, and estimated net carbs in grams.
```
*On CoT:* with a **reasoning model, do not add "think step by step"** — carb budgeting across nine meals with a variety constraint is precisely the kind of multi-constraint optimization these models handle better with a reasoning budget than with an imposed procedure. With a **small model, add explicit CoT**: instruct it to tally the running daily carb total after each meal, because without externalizing the arithmetic it will produce plans that are individually plausible and collectively over budget.

**2. Critique — with a rubric.**
```
You are a critical reviewer. Evaluate the plan against each check below and
return a finding for every one, marked PASS or FAIL with specifics.

1. CARB BUDGET: sum the stated carbs for each day. Is each day under 50g?
   Report the actual totals.
2. HIDDEN CARBS: for each meal, identify ingredients that commonly carry
   unstated carbs — potatoes, rice, corn, breading, glazes, sauces, dressings,
   marinades. Flag any meal whose stated figure looks implausible for its
   ingredients, and say why.
3. FISH: scan for fish, shellfish, fish sauce, Worcestershire, anchovy,
   oyster sauce, dashi. Flag any occurrence.
4. VARIETY: count appearances of each main protein. Flag any appearing 3+ times.
5. COMPLETENESS: confirm 3 meals × 3 days = 9 meals, all fields populated.
```
Every check is mechanical and produces a specific finding. Compare to "review this plan for problems," which produces a paragraph of agreeable observations.

**3. Revise + structure.** Final call takes the plan and the findings, and is forced into a schema:
```python
{"type": "object",
 "properties": {
   "Day1": {"$ref": "#/$defs/day"}, "Day2": {"$ref": "#/$defs/day"}, "Day3": {"$ref": "#/$defs/day"}},
 "$defs": {
   "day": {"type": "object",
     "properties": {"Breakfast": {"$ref": "#/$defs/meal"},
                    "Lunch": {"$ref": "#/$defs/meal"},
                    "Dinner": {"$ref": "#/$defs/meal"}},
     "required": ["Breakfast", "Lunch", "Dinner"]},
   "meal": {"type": "object",
     "properties": {"name": {"type": "string"},
                    "main_protein": {"type": "string"},
                    "est_carbs_g": {"type": "number"}},
     "required": ["name", "main_protein", "est_carbs_g"]}},
 "required": ["Day1", "Day2", "Day3"]}
```

#### **Example Solution — Part B: what self-critique can't catch**

**Why the critic missed it.** The critic and the planner share the same underlying knowledge. If the model believes a cauliflower-crust pizza is 8g of carbs, it believes that in *both* calls — the critic re-derives the same wrong number and marks it PASS. This is the structural ceiling from section 2: self-critique catches *inconsistency* (a stated 8g that contradicts a stated total) but not *shared false belief*. Note that check 2 was designed to catch exactly this and still failed, because the check asks the model to judge plausibility using the same faulty estimate.

**The external check.** Look every ingredient up in a real nutrition database:

```python
def verify_carbs(meal, nutrition_db, tolerance=0.25):
    ingredients = extract_ingredients(meal)              # a model call is fine here
    actual = sum(nutrition_db.lookup(i.name, i.grams).net_carbs for i in ingredients)
    if abs(actual - meal.est_carbs_g) > tolerance * max(actual, 1):
        return Finding("CARB_MISMATCH", meal=meal.name,
                       stated=meal.est_carbs_g, actual=actual)
```

**What it needs access to:** a ground-truth nutrition database (USDA FoodData Central or equivalent), and per-meal ingredients *with quantities* — which means the generation step must emit ingredients and grams, not just a meal name. That's a design consequence worth noticing: **the verification requirement reaches back and changes the schema of an earlier step.** Verification isn't something you bolt on at the end; it constrains the whole chain.

#### **Example Solution — Part C: routing**

| Step | Tier | Why |
| :--- | :--- | :--- |
| Generate | **Frontier** | Nine meals under three interacting hard constraints is genuine constrained optimization — the step where model quality shows up most |
| Critique | **Frontier** | A weak critic is worse than no critic: it produces PASS findings that create false confidence. If budget forces a downgrade, split it — mechanical checks (fish keywords, meal counts, arithmetic) go to code for free, and only plausibility judgments need a model |
| Structure/revise | **Cheap** | Reformatting known content into a schema is mechanical. The schema enforces the shape, so there's nothing left for a large model to contribute |

**Never route down: the critique** — for the reason above. The generation step degrading produces a visibly mediocre plan someone will notice. The critique step degrading produces a *confidently approved* bad plan, which is the failure mode that reaches the user.
