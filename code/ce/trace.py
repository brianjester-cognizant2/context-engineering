"""Tracing and token accounting.

Module 6, Lesson 2. The most useful single line in a trace is the *assembled
context* — what the model actually saw. Most teams log the query and the output
and not the thing in between, which leaves them inferring rather than reading.

Span names follow the OpenTelemetry GenAI conventions (`gen_ai.chat`,
`gen_ai.tool`, `gen_ai.agent`) so a trace exported from here is readable in any
OTLP backend. Those conventions are pre-stable, so the mapping lives in one
place — here — and a rename is a one-file change.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=time.monotonic)
    duration_s: float = 0.0

    def end(self, **attributes: Any) -> "Span":
        self.duration_s = time.monotonic() - self.started_at
        self.attributes.update(attributes)
        return self


@dataclass
class Trace:
    spans: list[Span] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0

    def span(self, name: str, /, **attributes: Any) -> Span:
        s = Span(name=name, attributes=dict(attributes))
        self.spans.append(s)
        return s

    def record_usage(self, *, input_tokens: int, output_tokens: int, cached: int = 0) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cached_tokens += cached

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def cost(self, *, input_per_m: float = 5.0, output_per_m: float = 25.0,
             cached_discount: float = 0.10) -> float:
        uncached = max(0, self.input_tokens - self.cached_tokens)
        return (
            uncached / 1_000_000 * input_per_m
            + self.cached_tokens / 1_000_000 * input_per_m * cached_discount
            + self.output_tokens / 1_000_000 * output_per_m
        )

    @property
    def cache_hit_rate(self) -> float:
        """Alert on this. A drop to zero is the only symptom of a broken cache prefix."""
        return self.cached_tokens / self.input_tokens if self.input_tokens else 0.0

    def tool_calls(self) -> list[Span]:
        return [s for s in self.spans if s.name == "gen_ai.tool"]

    def thrashing(self, *, threshold: int = 2) -> list[tuple[str, int]]:
        """Detect wasted tool calls: the same tool returning the same result.

        Keying on arguments alone is too strict — an agent that rephrases a
        search three times issues three *different* calls and looks fine. Keying
        on the tool name alone is too loose — reading ten different files is not
        thrashing. What is unambiguously wasted is the same tool returning a
        result it has already returned: three rephrasings of a query that surface
        the identical five articles taught the agent nothing on calls two and
        three.

        Returns (label, count) for each repeated (tool, result) pair.
        """
        counts: dict[str, int] = {}
        for span in self.tool_calls():
            name = span.attributes.get("name")
            digest = span.attributes.get("result_digest")
            if digest is None:
                continue
            key = f"{name}->{digest}"
            counts[key] = counts.get(key, 0) + 1
        return sorted(
            ((k, v) for k, v in counts.items() if v >= threshold),
            key=lambda kv: -kv[1],
        )

    def exact_repeats(self, *, threshold: int = 2) -> list[tuple[str, int]]:
        """Byte-identical repeated calls — the strictest, least arguable signal."""
        counts: dict[str, int] = {}
        for span in self.tool_calls():
            key = f"{span.attributes.get('name')}({span.attributes.get('arguments')})"
            counts[key] = counts.get(key, 0) + 1
        return sorted(
            ((k, v) for k, v in counts.items() if v >= threshold), key=lambda kv: -kv[1]
        )

    def render(self) -> str:
        lines = [
            f"trace: {len(self.spans)} spans  "
            f"in={self.input_tokens}  out={self.output_tokens}  "
            f"cached={self.cached_tokens} ({self.cache_hit_rate:.0%})  "
            f"cost≈${self.cost():.4f}"
        ]
        for span in self.spans:
            attrs = " ".join(f"{k}={v}" for k, v in span.attributes.items() if k != "context")
            lines.append(f"  {span.name:<16} {span.duration_s * 1000:7.1f}ms  {attrs}")
        return "\n".join(lines)
