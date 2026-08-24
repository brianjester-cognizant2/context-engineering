# Eval Set: <system name>

**Owner:** <a named person — unowned eval sets rot within a quarter>
**Cases:** <n> — **smallest detectable change:** ±<1.96 × sqrt(0.25/n)>%
**Last reviewed:**

> Under ~100 cases you cannot distinguish a real 10% improvement from noise.
> State plainly what this set can and cannot detect.

---

## Stratification

| Stratum | Target | Actual | Notes |
|---|---|---|---|
| Easy / happy path | 20% | | |
| Multi-step / synthesis | 25% | | |
| Unanswerable (system should say so) | 15% | | |
| Ambiguous (system should ask) | 10% | | |
| Adversarial / injection | 10% | | |
| **Past production failures** | 20% | | Every incident becomes a case, same day |

---

## Case format

```yaml
- id: dup-charge-01
  goal: "Why was I charged twice last month?"
  tags: [billing, multi-step, regression]
  ground_truth_answer: "Two identical charges on Jul 3; a duplicate."
  ground_truth_context:
    - "orders.csv rows 442-443 — identical amount, same timestamp"
  checks:
    - type: deterministic
      assert: "cited order ids exist in the retrieved set"
    - type: unit_test           # LMUnit style, judged
      question: "Does the response state the specific date of the duplicate?"
    - type: trajectory
      assert: "get_orders called before any search_kb call"
  known_failure_mode: "Agent searches the KB first and burns 3 turns."
```

---

## Metrics tracked

| Metric | Current | Threshold | Notes |
|---|---|---|---|
| Pass rate | | | |
| Context precision | | | |
| Context recall | | | |
| Faithfulness | | | |
| Answer relevance | | | |
| Trajectory: tool selection | | | |
| Trajectory: plan coherence | | | |
| Cost per case | | | |
| p50 / p95 latency | | | |

---

## Judge rubric (if using LLM-as-judge)

**Criterion:** <what is being judged>

```
Award one point for each, maximum <n>. Judge only what is present in the text.

+1  <binary, textually verifiable condition>
+1  <binary, textually verifiable condition>

Score 0 if none apply. Length is not a criterion.
```

**Calibration:** <n> hand-labeled examples — **Cohen's kappa: <x>**
Below ~0.6, fix the **rubric**, not the judge model.

**Biases controlled for:**
- Position — <randomize order / run both and average>
- Verbosity — <explicit "length is not a criterion"; include short-good and long-hollow examples>
- Self-preference — <use a different model family as judge>

---

## What this eval set cannot detect

<Be specific. This is the most useful section for whoever inherits the system.>
