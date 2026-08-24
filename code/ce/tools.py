"""Tools: schemas, dispatch, and errors the agent can act on.

Implements the principles from Module 5, Lesson 2:

* A tool description is prompt surface, so it carries a `when_to_use` clause.
* A tool error is never raised into the loop — it is returned as an observation
  the model can read and recover from on its next turn.
* Destructive tools are declared as such, so the harness can gate them rather
  than relying on the model to be careful.
* Results are size-aware: a tool that returns 8,000 tokens has spent a large
  slice of the context budget on one call.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable

from . import tokens


class ToolError(Exception):
    """Raised inside a tool implementation to signal an actionable failure.

    The `hint` is the important field. `ToolError("Not found")` teaches the
    agent nothing; `ToolError("No customer 'jon@acme'", hint="Try search_customers")`
    turns a dead end into a recovery.
    """

    def __init__(self, message: str, *, hint: str = "", data: Any = None):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.data = data


@dataclass(frozen=True)
class ToolResult:
    tool_call_id: str
    name: str
    content: Any
    is_error: bool = False
    tokens: int = 0

    def render(self) -> str:
        prefix = "ERROR: " if self.is_error else ""
        return f"{prefix}{self.content}"


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    fn: Callable[..., Any]
    required: tuple[str, ...] = ()
    when_to_use: str = ""
    destructive: bool = False
    max_result_tokens: int = 2_000

    def schema(self) -> dict[str, Any]:
        """The JSON Schema the model sees. This is prompt surface."""
        description = self.description
        if self.when_to_use:
            description = f"{description} {self.when_to_use}"
        return {
            "name": self.name,
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": list(self.required),
            },
        }

    def schema_tokens(self) -> int:
        s = self.schema()
        return tokens.count(str(s))


@dataclass
class ToolRegistry:
    tools: dict[str, Tool] = field(default_factory=dict)

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        *,
        required: tuple[str, ...] = (),
        when_to_use: str = "",
        destructive: bool = False,
        max_result_tokens: int = 2_000,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[name] = Tool(
                name=name,
                description=description,
                parameters=parameters,
                fn=fn,
                required=required,
                when_to_use=when_to_use,
                destructive=destructive,
                max_result_tokens=max_result_tokens,
            )
            return fn

        return decorator

    def add(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def schemas(self) -> list[dict[str, Any]]:
        return [t.schema() for t in self.tools.values()]

    def schema_tokens(self) -> int:
        """What your tool set costs in context, on every single turn."""
        return sum(t.schema_tokens() for t in self.tools.values())

    def dispatch(self, call_id: str, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool. Never raises — every failure becomes an observation.

        This is the single highest-value line in the module. An exception that
        propagates kills the run; an error the model can read is just another
        observation it can recover from.
        """
        tool = self.tools.get(name)
        if tool is None:
            available = ", ".join(sorted(self.tools)) or "(none)"
            return self._error(
                call_id,
                name,
                f"No tool named {name!r}.",
                hint=f"Available tools: {available}.",
            )

        missing = [p for p in tool.required if p not in arguments]
        unknown = [k for k in arguments if k not in tool.parameters]
        if missing or unknown:
            # Report BOTH when both apply. A typo like `e_mail` for `email` is
            # simultaneously a missing argument and an unknown one; reporting
            # only the first sends the agent chasing half the problem.
            problems = []
            if missing:
                problems.append(f"missing required argument(s): {', '.join(missing)}")
            if unknown:
                problems.append(f"unknown argument(s): {', '.join(unknown)}")
            return self._error(
                call_id,
                name,
                f"Invalid call to {name}: {'; '.join(problems)}.",
                hint=(
                    f"{name} accepts: {', '.join(tool.parameters) or '(no arguments)'}"
                    + (f"; required: {', '.join(tool.required)}." if tool.required else ".")
                ),
            )

        try:
            value = tool.fn(**arguments)
        except ToolError as exc:
            return self._error(call_id, name, exc.message, hint=exc.hint, data=exc.data)
        except TypeError as exc:
            return self._error(
                call_id, name, f"Invalid arguments: {exc}", hint=f"Signature: {_sig(tool.fn)}"
            )
        except Exception as exc:  # noqa: BLE001 - deliberate: nothing escapes into the loop
            return self._error(
                call_id,
                name,
                f"{type(exc).__name__}: {exc}",
                hint="This is an internal error, not a usage error. Try a different approach.",
            )

        rendered = value if isinstance(value, str) else str(value)
        n = tokens.count(rendered)
        if n > tool.max_result_tokens:
            value = _truncate_with_notice(rendered, tool.max_result_tokens, name)
            n = tokens.count(value)
        return ToolResult(tool_call_id=call_id, name=name, content=value, tokens=n)

    @staticmethod
    def _error(call_id: str, name: str, message: str, *, hint: str = "", data: Any = None) -> ToolResult:
        parts = [message]
        if hint:
            parts.append(f"Hint: {hint}")
        if data is not None:
            parts.append(f"Details: {data}")
        content = " ".join(parts)
        return ToolResult(
            tool_call_id=call_id,
            name=name,
            content=content,
            is_error=True,
            tokens=tokens.count(content),
        )


def _sig(fn: Callable[..., Any]) -> str:
    try:
        return f"{fn.__name__}{inspect.signature(fn)}"
    except (TypeError, ValueError):
        return fn.__name__


def _truncate_with_notice(text: str, budget_tokens: int, name: str) -> str:
    """Truncate an oversized result and tell the agent what happened.

    Silent truncation reads as 'this is the whole result', which is how an agent
    ends up confidently reasoning about the first 10% of a table.
    """
    keep_chars = budget_tokens * 4
    head = text[: int(keep_chars * 0.7)]
    tail = text[-int(keep_chars * 0.2) :]
    return (
        f"{head}\n\n...[TRUNCATED: {name} returned ~{tokens.count(text)} tokens, "
        f"over its {budget_tokens}-token limit. Showing the head and tail. "
        f"Narrow your query or request a specific range.]...\n\n{tail}"
    )
