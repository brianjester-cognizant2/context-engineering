"""The model interface, plus a deterministic mock.

Everything in this package runs offline against `MockModel`. That is not a
convenience — it is the point. A harness whose behaviour you can only observe by
spending money on a live API is a harness you cannot test, and an untested
harness is where the failures in Module 8, Lesson 1 come from.

`MockModel` is scriptable: you hand it the exact sequence of turns you want, so
a test can reproduce a specific agent trajectory byte for byte.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, Sequence

from . import tokens


@dataclass(frozen=True)
class ToolCall:
    """A model's request to invoke a tool."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ModelResponse:
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    input_tokens: int = 0
    output_tokens: int = 0
    # "tool_use" | "end_turn" | "max_tokens"
    stop_reason: str = "end_turn"

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class Model(Protocol):
    """Anything that can turn a context into a response."""

    def generate(
        self,
        *,
        system: str,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]] = (),
    ) -> ModelResponse: ...


@dataclass
class MockModel:
    """A deterministic model driven by a script or a policy function.

    Two modes:

    * `script`   — a fixed list of responses, returned in order. Once exhausted,
                   the model returns a plain end_turn. Use for reproducing an
                   exact trajectory in a test.
    * `policy`   — a callable receiving (turn_index, messages) and returning a
                   ModelResponse. Use when the response should depend on what
                   the tools returned.

    Records every call it receives, so a test can assert on what the *harness*
    actually sent — which is usually the thing that is wrong.
    """

    script: list[ModelResponse] = field(default_factory=list)
    policy: Callable[[int, Sequence[dict[str, Any]]], ModelResponse] | None = None
    calls: list[dict[str, Any]] = field(default_factory=list, init=False)

    def generate(
        self,
        *,
        system: str,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]] = (),
    ) -> ModelResponse:
        turn = len(self.calls)
        rendered = system + "".join(str(m.get("content", "")) for m in messages)
        self.calls.append(
            {"system": system, "messages": list(messages), "tools": list(tools)}
        )

        if self.policy is not None:
            response = self.policy(turn, messages)
        elif turn < len(self.script):
            response = self.script[turn]
        else:
            response = ModelResponse(text="(no further scripted turns)")

        # Fill in token accounting if the script did not specify it.
        if response.input_tokens == 0:
            response = ModelResponse(
                text=response.text,
                tool_calls=response.tool_calls,
                input_tokens=tokens.count(rendered),
                output_tokens=response.output_tokens or tokens.count(response.text),
                stop_reason=response.stop_reason,
            )
        return response


def say(text: str, *, stop: str = "end_turn") -> ModelResponse:
    """Shorthand: the model answers with text."""
    return ModelResponse(text=text, stop_reason=stop)


def call(name: str, /, _id: str = "", **arguments: Any) -> ModelResponse:
    """Shorthand: the model requests one tool call."""
    return ModelResponse(
        tool_calls=(ToolCall(id=_id or f"call_{name}", name=name, arguments=arguments),),
        stop_reason="tool_use",
    )
