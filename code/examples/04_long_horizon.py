"""Module 4 L4 — compaction, externalized state, and surviving a crash.

Run:  python3 examples/04_long_horizon.py
"""

import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce import CompactionPolicy, MockModel, Workspace, clear_stale_tool_results, compact, say
from ce import tokens as tok

# --- a trajectory that has grown ------------------------------------------
messages = [
    {"role": "system", "content": "You migrate test files."},
    {"role": "user", "content": "Migrate the suite from unittest to pytest."},
]
for i in range(20):
    messages.append({"role": "assistant", "content": f"Migrating tests/test_{i}.py"})
    messages.append({"role": "tool", "name": "read_file", "content": "x" * 3_000})

size = lambda ms: sum(tok.count(str(m["content"])) for m in ms)

print("=" * 72)
print("1. Clear stale tool results FIRST — no model call, no risk")
print("=" * 72)
print("before:            ", size(messages), "tokens")
cleared = clear_stale_tool_results(messages, keep_recent=2)
print("after clearing:    ", size(cleared), "tokens")
print(f"reduction:          {1 - size(cleared)/size(messages):.0%}, for zero model calls")
print("\nA file read 40 turns ago does not need its contents in context.")

print()
print("=" * 72)
print("2. Compaction preserves the head and the tail")
print("=" * 72)
model = MockModel(policy=lambda t, m: say(
    "GOAL: migrate unittest -> pytest. DONE: tests/test_0..19. "
    "DEAD END: bulk sed rewrite broke fixtures in test_7 and test_12 — do not retry. "
    "CONVENTION: fixtures use @pytest.fixture(scope='module')."))
result = compact(cleared, model=model, policy=CompactionPolicy(keep_head=2, keep_recent=4))
print("before:", result.tokens_before, "-> after:", result.tokens_after,
      f"({result.ratio:.0%})")
print("first message preserved:", result.messages[0]["content"][:40])
print("summary contains dead ends:", "DEAD END" in result.summary)

print()
print("=" * 72)
print("3. Compaction is lossy. State you cannot lose goes in a file.")
print("=" * 72)
with tempfile.TemporaryDirectory() as tmp:
    ws = Workspace(pathlib.Path(tmp))
    ws.set_goal("Migrate 400 test files from unittest to pytest.")
    ws.set_plan([{"id": f"test_{i}", "what": f"migrate tests/test_{i}.py",
                  "status": "done" if i < 3 else "todo"} for i in range(5)])
    ws.record_blocker("bulk sed rewrite", "broke fixtures in test_7 and test_12")

    print(ws.brief())
    print()
    print("  brief size:", tok.count(ws.brief()), "tokens — cheap enough to reload every turn")

    # simulate a crash: the entire conversation is gone
    print()
    print("=" * 72)
    print("4. The process is killed at file 300. What survives?")
    print("=" * 72)
    reopened = Workspace(pathlib.Path(tmp))
    print("  resumable:      ", reopened.is_resumable())
    print("  goal:           ", reopened.goal)
    print("  next todo:      ", next(s["id"] for s in reopened.plan() if s["status"] == "todo"))
    print("  won't retry:    ", "bulk sed rewrite" in reopened.read(Workspace.BLOCKERS))
    print()
    print("  Lost regardless: the working intuition about the file it was mid-way")
    print("  through. That is bounded and cheap — which is why it stays in context.")
