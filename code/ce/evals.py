"""An eval harness: quality scores, trajectory scores, and honest statistics.

Module 6, Lesson 1. Two things this deliberately makes hard to get wrong:

* **Trajectory scoring is separate from outcome scoring.** A single success rate
  tells you the agent got worse. Six dimensions tell you *tool selection* got
  worse after you added three tools — which is a fix, not an investigation.
* **Small eval sets announce their own uselessness.** `EvalReport` reports the
  smallest difference it could have detected, so nobody ships a regression on
  the strength of twenty cases.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence


@dataclass
class Case:
    id: str
    goal: str
    # Any tags you want to slice by: difficulty, task type, "regression".
    tags: tuple[str, ...] = ()
    expected: Any = None
    # A per-case check. Return True if the outcome is acceptable.
    check: Callable[[Any], bool] | None = None


TRAJECTORY_DIMENSIONS = (
    "tool_selection",
    "argument_extraction",
    "result_utilization",
    "error_recovery",
    "plan_coherence",
    "task_completion",
)


@dataclass
class TrajectoryScore:
    """Six dimensions, scored independently. 0.0-1.0 each, or None if N/A."""

    scores: dict[str, float | None] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)

    def set(self, dimension: str, score: float | None, note: str = "") -> None:
        if dimension not in TRAJECTORY_DIMENSIONS:
            raise ValueError(f"Unknown dimension {dimension!r}")
        self.scores[dimension] = score
        if note:
            self.notes[dimension] = note

    @property
    def mean(self) -> float | None:
        vals = [v for v in self.scores.values() if v is not None]
        return sum(vals) / len(vals) if vals else None


def score_trajectory(outcome: Any) -> TrajectoryScore:
    """Heuristic trajectory scoring from a trace.

    Cheap, deterministic signals only — the aim is to catch the failure patterns
    from Module 6, Lesson 2 without a model call. A model judge can layer on top
    for the qualitative dimensions.
    """
    score = TrajectoryScore()
    trace = outcome.trace
    tool_spans = trace.tool_calls()

    if not tool_spans:
        score.set("tool_selection", None, "no tools used")
        score.set("error_recovery", None, "no tool errors")
    else:
        thrash = trace.thrashing()
        wasted = sum(count - 1 for _, count in thrash)
        score.set(
            "tool_selection",
            max(0.0, 1.0 - wasted / len(tool_spans)),
            f"{wasted} redundant of {len(tool_spans)} calls" if wasted else "no thrashing",
        )

        errors = [s for s in tool_spans if s.attributes.get("is_error")]
        if errors:
            recovered = outcome.ok
            score.set(
                "error_recovery",
                1.0 if recovered else 0.0,
                f"{len(errors)} tool errors; {'recovered' if recovered else 'did not recover'}",
            )
        else:
            score.set("error_recovery", None, "no tool errors")

    bad_args = [s for s in tool_spans if "Missing required" in str(s.attributes)]
    score.set("argument_extraction", 0.0 if bad_args else 1.0)

    score.set("task_completion", 1.0 if outcome.ok else 0.0, outcome.reason)
    score.set(
        "plan_coherence",
        max(0.0, 1.0 - outcome.iterations / 25),
        f"{outcome.iterations} iterations",
    )
    score.set("result_utilization", None, "requires a judge or a human")
    return score


@dataclass
class CaseResult:
    case: Case
    passed: bool
    outcome: Any
    trajectory: TrajectoryScore
    error: str = ""


@dataclass
class EvalReport:
    results: list[CaseResult]

    @property
    def n(self) -> int:
        return len(self.results)

    @property
    def pass_rate(self) -> float:
        return sum(r.passed for r in self.results) / self.n if self.n else 0.0

    @property
    def detectable_delta(self) -> float:
        """The smallest pass-rate change this eval set could distinguish from noise.

        Roughly a 95% binomial margin at p=0.5. With 20 cases it is ~22 points,
        which is why a 20-case set cannot tell you a 10% improvement happened.
        """
        return 1.96 * math.sqrt(0.25 / self.n) if self.n else 1.0

    def by_dimension(self) -> dict[str, float | None]:
        out: dict[str, float | None] = {}
        for dim in TRAJECTORY_DIMENSIONS:
            vals = [
                r.trajectory.scores.get(dim)
                for r in self.results
                if r.trajectory.scores.get(dim) is not None
            ]
            out[dim] = sum(vals) / len(vals) if vals else None
        return out

    def by_tag(self) -> dict[str, float]:
        tags: dict[str, list[bool]] = {}
        for r in self.results:
            for tag in r.case.tags:
                tags.setdefault(tag, []).append(r.passed)
        return {t: sum(v) / len(v) for t, v in tags.items()}

    def total_cost(self) -> float:
        return sum(r.outcome.trace.cost() for r in self.results if r.outcome)

    def render(self) -> str:
        lines = [
            f"cases: {self.n}   pass rate: {self.pass_rate:.0%}",
            f"smallest detectable change: ±{self.detectable_delta:.0%}"
            + ("   <-- TOO SMALL TO MAKE SHIP DECISIONS FROM" if self.n < 100 else ""),
            f"total cost: ${self.total_cost():.4f}",
            "",
            "trajectory dimensions:",
        ]
        for dim, val in self.by_dimension().items():
            lines.append(f"  {dim:<22} {'n/a' if val is None else f'{val:.2f}'}")
        if by_tag := self.by_tag():
            lines.append("")
            lines.append("by tag:")
            for tag, rate in sorted(by_tag.items()):
                lines.append(f"  {tag:<22} {rate:.0%}")
        if failures := [r for r in self.results if not r.passed]:
            lines.append("")
            lines.append("failures:")
            for r in failures:
                lines.append(f"  {r.case.id}: {r.error or r.outcome.reason}")
        return "\n".join(lines)


def run_eval(cases: Sequence[Case], runner: Callable[[Case], Any]) -> EvalReport:
    """Run every case, scoring outcome and trajectory separately."""
    results: list[CaseResult] = []
    for case in cases:
        try:
            outcome = runner(case)
        except Exception as exc:  # noqa: BLE001
            results.append(
                CaseResult(case, False, None, TrajectoryScore(), f"{type(exc).__name__}: {exc}")
            )
            continue
        passed = case.check(outcome) if case.check else outcome.ok
        results.append(CaseResult(case, bool(passed), outcome, score_trajectory(outcome)))
    return EvalReport(results)


# -- judge calibration -----------------------------------------------------


def cohens_kappa(human: Sequence[int], judge: Sequence[int]) -> float:
    """Agreement between a judge and human labels, corrected for chance.

    An uncalibrated judge is a random number generator with good manners. Below
    about 0.6 here, fix the *rubric* — it is almost never the judge model.
    """
    if len(human) != len(judge) or not human:
        raise ValueError("label sequences must be the same non-zero length")
    n = len(human)
    observed = sum(h == j for h, j in zip(human, judge)) / n
    labels = set(human) | set(judge)
    expected = sum(
        (sum(h == lbl for h in human) / n) * (sum(j == lbl for j in judge) / n) for lbl in labels
    )
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0
