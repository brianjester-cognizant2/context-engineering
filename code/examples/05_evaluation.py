"""Module 6 L1 — trajectory evals, eval-set sizing, and judge calibration.

Run:  python3 examples/05_evaluation.py
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce import (
    AgentLoop, Case, Deterministic, Guardrails, MockModel, ToolRegistry,
    call, cohens_kappa, run_eval, say,
)

reg = ToolRegistry()


@reg.register("search_kb", "Search the knowledge base.",
              {"q": {"type": "string"}}, required=("q",))
def search_kb(q: str) -> str:
    # Realistically, three rephrasings of the same question surface the same
    # five generic articles. That is what makes calls 2 and 3 pure waste.
    return "5 generic billing articles: 'About charges', 'Billing FAQ', ..."


@reg.register("get_orders", "Get a customer's orders.",
              {"customer": {"type": "string"}}, required=("customer",))
def get_orders(customer: str) -> str:
    return "2 identical charges on Jul 3"


def make_runner(script):
    def runner(case: Case):
        return AgentLoop(
            model=MockModel(script=list(script)),
            tools=reg,
            verifier=Deterministic(lambda s: bool(s.artefact), "produced an answer"),
            guardrails=Guardrails(max_iterations=12, no_progress_after=99),
        ).run(case.goal)
    return runner


print("=" * 72)
print("1. The trajectory is the unit, not the answer")
print("=" * 72)

good = [call("get_orders", customer="c1"), say("Two identical charges on Jul 3 — duplicate.")]
lucky = [call("search_kb", q="double charge"), call("search_kb", q="duplicate charge"),
         call("search_kb", q="charged twice"), call("get_orders", customer="c1"),
         say("Two identical charges on Jul 3 — duplicate.")]

for label, script in [("efficient", good), ("lucky (thrashes first)", lucky)]:
    report = run_eval([Case(id="dup", goal="Why was I charged twice?")], make_runner(script))
    dims = report.by_dimension()
    print(f"\n  {label}:")
    print(f"    task_completion  {dims['task_completion']:.2f}   <- identical")
    print(f"    tool_selection   {dims['tool_selection']:.2f}")
    print(f"    plan_coherence   {dims['plan_coherence']:.2f}")

print("\n  Same final answer, same completion score. Only the trajectory dimensions")
print("  reveal that one of them got there by luck and will fail on a harder case.")

print()
print("=" * 72)
print("2. Eval-set size decides what you can detect")
print("=" * 72)
for n in (20, 100, 500):
    cases = [Case(id=f"c{i}", goal="q", tags=("easy" if i % 3 else "hard",)) for i in range(n)]
    report = run_eval(cases, make_runner(good))
    verdict = "cannot make ship decisions" if n < 100 else "usable"
    print(f"  n={n:<4} smallest detectable change: ±{report.detectable_delta:.0%}   {verdict}")
print("\n  With 20 cases, a real 10% improvement is indistinguishable from noise.")

print()
print("=" * 72)
print("3. Judge calibration: 80% agreement, zero signal")
print("=" * 72)
human = [1] * 8 + [0] * 2          # 8 good responses, 2 bad
judge = [1] * 10                   # a judge that always says PASS
raw = sum(h == j for h, j in zip(human, judge)) / len(human)
print(f"  raw agreement: {raw:.0%}   <- looks fine on a dashboard")
print(f"  Cohen's kappa: {cohens_kappa(human, judge):.2f}   <- chance-level: no signal at all")
print("\n  The judge never caught a single failure. Raw agreement cannot tell you that.")
print("  Below ~0.6 kappa, fix the RUBRIC — it is almost never the judge model.")

print()
print("=" * 72)
print("4. The full report")
print("=" * 72)
cases = [Case(id=f"c{i}", goal="q", tags=("easy" if i % 3 else "hard",)) for i in range(40)]
print(run_eval(cases, make_runner(lucky)).render())
