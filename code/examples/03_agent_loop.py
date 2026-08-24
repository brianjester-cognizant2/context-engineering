"""Module 8 L1-L2 — the harness, demonstrated as two runs of the same model.

Same model. Same task. The only difference is the harness around it.

Run:  python3 examples/03_agent_loop.py
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ce import (
    AgentLoop, Deterministic, Guardrails, MockModel, ToolError, ToolRegistry, call, say,
)

# --- the world the agent acts on -----------------------------------------
STATE = {"tests_pass": False, "patch_applied": False}


def build_tools() -> ToolRegistry:
    reg = ToolRegistry()

    @reg.register("run_tests", "Runs the test suite. Returns PASS or the failure.", {})
    def run_tests() -> str:
        if STATE["tests_pass"]:
            return "PASS: 41 passed"
        return "FAIL: test_checkout — assert 10.79 == 10.80"

    @reg.register(
        "apply_patch",
        "Applies a unified diff to a file under src/.",
        {"diff": {"type": "string", "description": "A unified diff."}},
        required=("diff",),
    )
    def apply_patch(diff: str) -> str:
        if "round" not in diff:
            raise ToolError(
                "Patch applied but tests still fail.",
                hint="The failure is a rounding error in the tax calculation.",
            )
        STATE["patch_applied"] = True
        STATE["tests_pass"] = True
        return "Patch applied to src/checkout.py (3 lines)."

    return reg


VERIFIER = Deterministic(lambda s: STATE["tests_pass"], "test suite passes")


def reset():
    STATE.update(tests_pass=False, patch_applied=False)


print("=" * 72)
print("HARNESS A — the notebook version: the model decides when it is done")
print("=" * 72)
reset()
confident = MockModel(policy=lambda turn, msgs: say(
    "I've fixed the bug — the tax calculation was rounding incorrectly. "
    "All tests should pass now."))
loop = AgentLoop(
    model=confident, tools=build_tools(), verifier=VERIFIER,
    guardrails=Guardrails(max_iterations=3, no_progress_after=99),
)
outcome = loop.run("The test_checkout test is failing. Fix it.")
print("model said:  ", outcome.state.artefact)
print("outcome:     ", outcome)
print("tests pass?  ", STATE["tests_pass"])
print("\nVictory declaration bias: the model asserts completion on every turn and")
print("never runs the tests. Nothing about the claim is checkable from the text —")
print("only the verifier, which inspects the world, can tell. It said no, 3 times.")

print()
print("=" * 72)
print("HARNESS B — same model, verification gates termination")
print("=" * 72)
reset()
diligent = MockModel(script=[
    call("run_tests"),
    call("apply_patch", diff="- return round(x, 1)\n+ return round(x, 2)"),
    call("run_tests"),
    say("Fixed: the tax calculation rounded to 1dp instead of 2."),
])
loop = AgentLoop(
    model=diligent, tools=build_tools(), verifier=VERIFIER,
    guardrails=Guardrails(max_iterations=8, no_progress_after=99),
)
outcome = loop.run("The test_checkout test is failing. Fix it.")
print("outcome:     ", outcome)
print("tests pass?  ", STATE["tests_pass"])
print()
print(outcome.trace.render())
print()
print("Note the loop exited at iteration 2, before the model's scripted third turn.")
print("The verifier checks the WORLD, so once the tests passed there was nothing")
print("left to do — the agent's own opinion was never consulted.")

print()
print("=" * 72)
print("GUARDRAILS — each failure mode has a structural stop")
print("=" * 72)
for label, model, rails in [
    ("stuck (no progress)", MockModel(policy=lambda t, m: say("still thinking")),
     Guardrails(max_iterations=50, no_progress_after=3)),
    ("thrashing (iteration cap)", MockModel(policy=lambda t, m: call("run_tests")),
     Guardrails(max_iterations=6, no_progress_after=99)),
    ("runaway (token budget)", MockModel(policy=lambda t, m: say("x" * 20_000)),
     Guardrails(max_iterations=99, max_tokens=30_000, no_progress_after=99)),
]:
    reset()
    o = AgentLoop(model=model, tools=build_tools(), verifier=VERIFIER,
                  guardrails=rails).run("fix it")
    print(f"  {label:<28} -> {o.reason}  (after {o.iterations} iterations)")

print("\nEvery exit hands a human the state and a reason. None of them run forever.")
