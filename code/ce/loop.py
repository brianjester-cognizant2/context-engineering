"""The agent loop, with the guardrails that separate a demo from a system.

Module 8, Lessons 1 and 2. Five features make the difference, and all five live
in the harness rather than the model:

1. An **iteration cap**.
2. A **token budget**, enforced before each call rather than after the bill.
3. **Errors returned, never raised** — a tool failure is an observation.
4. **No-progress detection** — stops a *stuck* loop immediately, where a cost cap
   would only stop a *runaway* loop eventually.
5. **External verification** — the loop exits when a verifier says the goal is
   met, not when the model says it is finished.

Every non-success exit escalates with the accumulated state and a reason. A loop
that fails silently is worse than one that never ran.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from . import tokens
from .compaction import CompactionPolicy, clear_stale_tool_results, compact
from .context import AssembledContext, ContextAssembler, Section, Stability
from .model import Model, ModelResponse
from .tools import ToolRegistry, ToolResult
from .trace import Trace
from .verify import Tier, Verdict, Verifier


class ApprovalDenied(Exception):
    pass


@dataclass
class Guardrails:
    max_iterations: int = 25
    max_tokens: int = 500_000
    max_tool_errors: int = 5
    no_progress_after: int = 3
    max_cost_usd: float | None = None


@dataclass
class AgentState:
    goal: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    artefact: Any = None
    scratch: dict[str, Any] = field(default_factory=dict)

    def signature(self) -> str:
        """A fingerprint of meaningful state, for no-progress detection.

        Deliberately excludes the message list — an agent re-reading the same
        file produces new messages while making no progress, and that is exactly
        the case this needs to catch.
        """
        payload = repr(self.artefact) + repr(sorted(self.scratch.items()))
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class Outcome:
    status: str  # "success" | "escalated"
    reason: str
    state: AgentState
    trace: Trace
    iterations: int
    verdict: Verdict | None = None

    @property
    def ok(self) -> bool:
        return self.status == "success"

    def __str__(self) -> str:
        return f"[{self.status}] {self.reason} after {self.iterations} iterations"


ApprovalFn = Callable[[str, dict[str, Any]], bool]


def _deny_all(name: str, arguments: dict[str, Any]) -> bool:
    """The safe default. A destructive tool with no approver is not callable."""
    return False


class AgentLoop:
    def __init__(
        self,
        *,
        model: Model,
        tools: ToolRegistry,
        verifier: Verifier,
        system_prompt: str = "You are a careful assistant.",
        guardrails: Guardrails | None = None,
        assembler: ContextAssembler | None = None,
        compaction: CompactionPolicy | None = None,
        approve: ApprovalFn = _deny_all,
        allow_self_report: bool = False,
    ) -> None:
        if not allow_self_report and getattr(verifier, "tier", Tier.SELF_REPORT) >= Tier.SELF_REPORT:
            raise ValueError(
                "Refusing to build a loop that terminates on the model's self-report. "
                "Supply a deterministic verifier, a judge, or a human gate — or pass "
                "allow_self_report=True if you genuinely mean it."
            )
        self.model = model
        self.tools = tools
        self.verifier = verifier
        self.system_prompt = system_prompt
        self.guardrails = guardrails or Guardrails()
        self.assembler = assembler or ContextAssembler()
        self.compaction = compaction or CompactionPolicy()
        self.approve = approve

    # -- public ------------------------------------------------------------

    def run(self, goal: str, *, extra_sections: Sequence[Section] = ()) -> Outcome:
        state = AgentState(goal=goal)
        trace = Trace()
        consecutive_tool_errors = 0
        unchanged_iterations = 0
        last_signature = state.signature()

        agent_span = trace.span("gen_ai.agent", goal=goal[:80])

        for iteration in range(1, self.guardrails.max_iterations + 1):
            over, why = self._over_budget(trace)
            if over:
                agent_span.end(status="escalated")
                return Outcome("escalated", why, state, trace, iteration - 1)

            context = self._assemble(state, extra_sections)
            response = self._call_model(context, trace)

            state.messages.append({"role": "assistant", "content": response.text})

            if response.tool_calls:
                results, errors = self._run_tools(response, state, trace)
                consecutive_tool_errors = consecutive_tool_errors + errors if errors else 0
                if consecutive_tool_errors >= self.guardrails.max_tool_errors:
                    agent_span.end(status="escalated")
                    return Outcome(
                        "escalated",
                        f"tool circuit breaker tripped after {consecutive_tool_errors} "
                        f"consecutive errors",
                        state,
                        trace,
                        iteration,
                    )
                for result in results:
                    state.messages.append(
                        {"role": "tool", "name": result.name, "content": result.render()}
                    )
            else:
                # No tool calls means the model believes it is finished.
                # That belief is an input to verification, never the exit itself.
                state.artefact = response.text

            # --- external verification decides, not the model -------------
            verdict = self.verifier.check(state)
            if verdict.met:
                agent_span.end(status="success", iterations=iteration)
                return Outcome("success", verdict.reason or "goal verified", state, trace,
                               iteration, verdict)

            # --- no-progress detection ------------------------------------
            signature = state.signature()
            unchanged_iterations = unchanged_iterations + 1 if signature == last_signature else 0
            last_signature = signature
            if unchanged_iterations >= self.guardrails.no_progress_after:
                agent_span.end(status="escalated")
                return Outcome(
                    "escalated",
                    f"no progress for {unchanged_iterations} iterations — likely stuck",
                    state,
                    trace,
                    iteration,
                    verdict,
                )

            self._maybe_compact(state, trace)

        agent_span.end(status="escalated")
        return Outcome(
            "escalated",
            f"iteration cap ({self.guardrails.max_iterations}) reached",
            state,
            trace,
            self.guardrails.max_iterations,
        )

    # -- internals ---------------------------------------------------------

    def _over_budget(self, trace: Trace) -> tuple[bool, str]:
        if trace.total_tokens > self.guardrails.max_tokens:
            return True, (
                f"token budget exhausted ({trace.total_tokens} > "
                f"{self.guardrails.max_tokens})"
            )
        if self.guardrails.max_cost_usd is not None and trace.cost() > self.guardrails.max_cost_usd:
            return True, f"cost ceiling exceeded (${trace.cost():.2f})"
        return False, ""

    def _assemble(self, state: AgentState, extra: Sequence[Section]) -> AssembledContext:
        sections: list[Section] = [
            Section("system", self.system_prompt, Stability.STATIC, value=100, droppable=False),
            Section("tools", str(self.tools.schemas()), Stability.STATIC, value=100, droppable=False),
            *extra,
            Section(
                "history",
                "\n".join(f"[{m['role']}] {m.get('content', '')}" for m in state.messages),
                Stability.RECENT,
                value=40,
            ),
            # The goal is volatile in position but must never be dropped —
            # which is precisely why value and stability are separate axes.
            Section("task", state.goal, Stability.VOLATILE, value=100, droppable=False),
        ]
        return self.assembler.assemble(sections)

    def _call_model(self, context: AssembledContext, trace: Trace) -> ModelResponse:
        span = trace.span("gen_ai.chat")
        response = self.model.generate(
            system=self.system_prompt,
            messages=[{"role": "user", "content": context.text}],
            tools=self.tools.schemas(),
        )
        # Anything at or above the cache breakpoint bills at the cached rate on
        # every turn after the first.
        cached = context.stable_tokens if trace.spans and len(trace.spans) > 2 else 0
        trace.record_usage(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cached=min(cached, response.input_tokens),
        )
        span.end(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            stop_reason=response.stop_reason,
            context_tokens=context.tokens,
            context_breakdown=context.breakdown(),
        )
        return response

    def _run_tools(
        self, response: ModelResponse, state: AgentState, trace: Trace
    ) -> tuple[list[ToolResult], int]:
        results: list[ToolResult] = []
        errors = 0
        for call in response.tool_calls:
            span = trace.span("gen_ai.tool", name=call.name, arguments=str(call.arguments))
            tool = self.tools.tools.get(call.name)

            if tool is not None and tool.destructive and not self.approve(call.name, call.arguments):
                result = ToolResult(
                    tool_call_id=call.id,
                    name=call.name,
                    content=(
                        f"Refused: {call.name} is irreversible and was not approved. "
                        f"Propose the action and explain why it is needed instead."
                    ),
                    is_error=True,
                    tokens=tokens.count(call.name) + 30,
                )
            else:
                result = self.tools.dispatch(call.id, call.name, call.arguments)

            errors += int(result.is_error)
            state.scratch[f"tool:{call.name}:{call.id}"] = str(result.content)[:200]
            results.append(result)
            span.end(
                is_error=result.is_error,
                result_tokens=result.tokens,
                result_digest=hashlib.sha256(str(result.content).encode()).hexdigest()[:12],
            )
        return results, errors

    def _maybe_compact(self, state: AgentState, trace: Trace) -> None:
        current = sum(tokens.count(str(m.get("content", ""))) for m in state.messages)
        if not self.compaction.should_compact(current):
            return
        span = trace.span("ce.compaction", before=current)
        # Cheapest first: clear stale tool results before summarizing anything.
        state.messages = clear_stale_tool_results(state.messages)
        after_clear = sum(tokens.count(str(m.get("content", ""))) for m in state.messages)
        if self.compaction.should_compact(after_clear):
            result = compact(state.messages, model=self.model, policy=self.compaction)
            state.messages = result.messages
            span.end(after=result.tokens_after, method="summarize")
        else:
            span.end(after=after_clear, method="clear_tool_results")
