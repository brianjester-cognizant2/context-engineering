"""Compaction: summarizing a trajectory to survive a long run.

Module 4, Lesson 3. Two decisions do all the work:

* **When.** At ~70% of the *effective* window, not 95%. By 95% you have already
  spent half the run in the degradation zone.
* **What to preserve.** The prompt below is the contract. Item 4 (dead ends) is
  the one people omit, and omitting it produces an agent that retries a failed
  approach, discovers it fails, and compacts that away too.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from . import tokens
from .model import Model

COMPACTION_PROMPT = """\
Summarize the agent's work so far, preserving ALL of the following. Omitting any
of these will cause the agent to repeat work or lose the thread.

1. The original goal, verbatim.
2. Decisions made, and the reason for each.
3. Findings — facts discovered, with where they came from.
4. Dead ends — what was tried, that it failed, and WHY. Without this the agent
   will retry them.
5. Open questions and remaining work.
6. Exact identifiers encountered: file paths, IDs, URLs, error strings, version
   numbers. Reproduce these EXACTLY; do not paraphrase.

Omit: verbose tool output, superseded intermediate reasoning, pleasantries.

<trajectory>
{trajectory}
</trajectory>"""


@dataclass
class CompactionPolicy:
    # Fraction of the EFFECTIVE window, not the nominal one.
    trigger_at: float = 0.70
    # Effective context is commonly 60-70% of nominal (Module 4, Lesson 1).
    effective_fraction: float = 0.65
    nominal_window: int = 200_000
    # Turns kept verbatim after the summary. Recent detail matters and
    # paraphrase loses it.
    keep_recent: int = 6
    # Turns pinned at the start regardless (system + original task).
    keep_head: int = 2

    @property
    def threshold_tokens(self) -> int:
        return int(self.nominal_window * self.effective_fraction * self.trigger_at)

    def should_compact(self, current_tokens: int) -> bool:
        return current_tokens >= self.threshold_tokens


@dataclass
class CompactionResult:
    messages: list[dict[str, Any]]
    summary: str
    tokens_before: int
    tokens_after: int
    compacted_turns: int

    @property
    def ratio(self) -> float:
        return self.tokens_after / self.tokens_before if self.tokens_before else 1.0


def clear_stale_tool_results(
    messages: Sequence[dict[str, Any]], *, keep_recent: int = 4
) -> list[dict[str, Any]]:
    """Low-risk compaction: replace old tool results with a one-line reference.

    Do this before summarizing anything. It requires no model call, cannot lose
    a decision, and is frequently the single largest available win — a file read
    forty turns ago does not need its full contents in context.
    """
    out: list[dict[str, Any]] = []
    tool_indices = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
    keep = set(tool_indices[-keep_recent:])
    for i, message in enumerate(messages):
        if message.get("role") == "tool" and i not in keep:
            name = message.get("name", "tool")
            n = tokens.count(str(message.get("content", "")))
            out.append(
                {
                    "role": "tool",
                    "name": name,
                    "content": f"[cleared: {name} returned ~{n} tokens earlier in this run]",
                }
            )
        else:
            out.append(dict(message))
    return out


def compact(
    messages: Sequence[dict[str, Any]],
    *,
    model: Model,
    policy: CompactionPolicy | None = None,
) -> CompactionResult:
    """Summarize the middle of a trajectory, keeping the head and the tail."""
    policy = policy or CompactionPolicy()
    before = sum(tokens.count(str(m.get("content", ""))) for m in messages)

    head = list(messages[: policy.keep_head])
    tail = list(messages[-policy.keep_recent :]) if policy.keep_recent else []
    middle = list(messages[policy.keep_head : len(messages) - len(tail)])

    if not middle:
        return CompactionResult(list(messages), "", before, before, 0)

    trajectory = "\n".join(
        f"[{m.get('role', '?')}] {m.get('content', '')}" for m in middle
    )
    response = model.generate(
        system="You compact agent trajectories without losing critical state.",
        messages=[{"role": "user", "content": COMPACTION_PROMPT.format(trajectory=trajectory)}],
    )
    summary = response.text

    rebuilt = head + [{"role": "user", "content": f"<prior_work>\n{summary}\n</prior_work>"}] + tail
    after = sum(tokens.count(str(m.get("content", ""))) for m in rebuilt)
    return CompactionResult(rebuilt, summary, before, after, len(middle))
