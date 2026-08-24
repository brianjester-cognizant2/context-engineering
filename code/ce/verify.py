"""Verification: deciding whether the goal was actually met.

Module 8, Lesson 2. The single rule: **the agent must not be the sole judge of
whether the agent succeeded.**

Verifiers are ranked by reliability, and the ranking is enforced — a Verifier
declares its tier, so a harness can refuse to terminate on self-report alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Protocol, Sequence


class Tier(IntEnum):
    """Lower is better. Prefer the lowest tier your goal permits."""

    DETERMINISTIC = 1  # tests pass, schema validates, row count matches
    JUDGE = 2          # a separate model with its own context and a rubric
    HUMAN = 3          # a person looks at the evidence
    SELF_REPORT = 4    # "I believe I'm done" — never sufficient alone


@dataclass(frozen=True)
class Verdict:
    met: bool
    tier: Tier
    reason: str = ""
    evidence: Any = None


class Verifier(Protocol):
    tier: Tier

    def check(self, state: Any) -> Verdict: ...


@dataclass
class Deterministic:
    """Wraps a predicate that inspects the world, not the transcript.

    Prefer this always. Designing a goal so a tier-1 check is *possible* is the
    practical craft of loop engineering — usually five minutes of thought that
    saves a week of unreliable runs.
    """

    predicate: Callable[[Any], bool]
    description: str = "deterministic check"
    tier: Tier = Tier.DETERMINISTIC

    def check(self, state: Any) -> Verdict:
        try:
            ok = bool(self.predicate(state))
        except Exception as exc:  # noqa: BLE001
            return Verdict(False, self.tier, f"check raised {type(exc).__name__}: {exc}")
        return Verdict(ok, self.tier, self.description)


@dataclass
class JudgeModel:
    """A separate model call with its own context and an explicit rubric.

    Note that it receives only the artefact and the rubric — not the agent's
    reasoning trace. A judge shown the agent's own justification tends to adopt
    it, which is how you get a judge that always agrees.
    """

    model: Any
    rubric: str
    tier: Tier = Tier.JUDGE

    def check(self, state: Any) -> Verdict:
        artefact = getattr(state, "artefact", None) or str(state)
        response = self.model.generate(
            system=(
                "You evaluate whether a goal was met. Answer with PASS or FAIL on "
                "the first line, then one sentence of justification. Judge only "
                "the artefact against the rubric."
            ),
            messages=[
                {"role": "user", "content": f"<rubric>{self.rubric}</rubric>\n<artefact>{artefact}</artefact>"}
            ],
        )
        met = response.text.strip().upper().startswith("PASS")
        return Verdict(met, self.tier, response.text.strip()[:200])


@dataclass
class All:
    """Every verifier must pass. Reports the strictest tier that was applied."""

    verifiers: Sequence[Verifier]

    @property
    def tier(self) -> Tier:
        return min((v.tier for v in self.verifiers), default=Tier.SELF_REPORT)

    def check(self, state: Any) -> Verdict:
        for verifier in self.verifiers:
            verdict = verifier.check(state)
            if not verdict.met:
                return verdict
        return Verdict(True, self.tier, "all checks passed")


@dataclass
class NeverTrustSelfReport:
    """A guard you can wrap around any verifier.

    Raises if the only available evidence is the model's own claim. Use it to
    make 'the loop must not exit on self-report' a property of the code rather
    than a line in a design document.
    """

    inner: Verifier

    @property
    def tier(self) -> Tier:
        return self.inner.tier

    def check(self, state: Any) -> Verdict:
        if self.inner.tier >= Tier.SELF_REPORT:
            raise ValueError(
                "Refusing to terminate on self-report. Supply a deterministic "
                "check, a judge, or a human gate."
            )
        return self.inner.check(state)
