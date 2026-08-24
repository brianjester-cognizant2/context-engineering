"""Module 1 L2 + Module 4 L1 + Module 8 L4 — cache-aware, budgeted assembly.

Run:  python3 examples/01_context_and_cache.py
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


from ce import Budget, CacheOrderError, ContextAssembler, Section, Stability, edge_load

print("=" * 72)
print("1. The ordering rule: stable -> volatile")
print("=" * 72)

asm = ContextAssembler(Budget(total=8_000))
ctx = asm.assemble([
    Section("task", "Summarize Q2 revenue.", Stability.VOLATILE, value=100, droppable=False),
    Section("docs", "Q2 revenue was $4.2M...", Stability.RETRIEVED, value=60),
    Section("system", "You are a financial analyst. Cite every figure.",
            Stability.STATIC, value=100, droppable=False),
    Section("memory", "This company reports in USD, fiscal year starts in April.",
            Stability.DURABLE, value=80),
])
print("order:      ", " -> ".join(s.name for s in ctx.sections))
print("breakpoint: ", ctx.cache_breakpoint_after, "(everything above caches)")
print("stable:     ", ctx.stable_tokens, "tokens billed at ~10% after turn 1")
print("breakdown:  ", ctx.breakdown())

print()
print("=" * 72)
print("2. The expensive silent bug: a timestamp mislabelled as STATIC")
print("=" * 72)
audited = ContextAssembler(Budget(total=8_000))
for turn, clock in enumerate(["11:03:07Z", "11:03:12Z", "11:03:19Z"], start=1):
    out = audited.assemble([
        Section("system", f"You are helpful. Current time: {clock}", Stability.STATIC),
        Section("task", f"turn {turn}", Stability.VOLATILE, droppable=False),
    ])
    status = "cached" if out.cache_prefix_stable else "PREFIX DIED — billing at full rate"
    print(f"  turn {turn}: {status}")
print(f"\n  cache_prefix_breaks = {audited.cache_prefix_breaks}")
print("\nNothing errors in production. No exception, no wrong answer — just a bill")
print("several times the estimate. Alert on cache hit rate; it is the only symptom.")

strict = ContextAssembler(strict_cache=True)
strict.assemble([Section("system", "build 1", Stability.STATIC)])
try:
    strict.assemble([Section("system", "build 2", Stability.STATIC)])
except CacheOrderError as exc:
    print("\nstrict_cache=True in development:\n  REFUSED:", str(exc)[:88], "...")

print()
print("=" * 72)
print("3. Over budget: drop by VALUE, not by age")
print("=" * 72)
asm = ContextAssembler(Budget(total=1_200, response_headroom=200))
ctx = asm.assemble([
    Section("goal_from_turn_1", "Find why EU checkout fails." + " " * 3_000,
            Stability.DURABLE, value=95),
    Section("chatter_from_turn_40", "ok sounds good" + " " * 3_000,
            Stability.RECENT, value=5),
    Section("task", "continue", Stability.VOLATILE, value=100, droppable=False),
])
print("kept:   ", [s.name for s in ctx.sections])
print("dropped:", [s.name for s in ctx.dropped])
print("\nA naive 'truncate oldest' would have dropped the goal and kept the chatter.")

print()
print("=" * 72)
print("4. Edge-loading ranked documents")
print("=" * 72)
ranked = ["best", "2nd", "3rd", "4th", "worst"]
print("ranked: ", ranked)
print("placed: ", edge_load(ranked))
print("\nBest first, second-best last — both high-attention. Weakest buried mid-context.")
