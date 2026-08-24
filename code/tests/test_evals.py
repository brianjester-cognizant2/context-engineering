"""Tests for the eval harness (Module 6, Lesson 1)."""

import unittest

from ce import (
    AgentLoop,
    Case,
    Deterministic,
    Guardrails,
    MockModel,
    ToolRegistry,
    call,
    cohens_kappa,
    run_eval,
    say,
)
from ce.evals import TRAJECTORY_DIMENSIONS


def registry() -> ToolRegistry:
    reg = ToolRegistry()

    @reg.register("search", "Searches.", {"q": {"type": "string"}}, required=("q",))
    def search(q: str) -> str:
        return f"results for {q}"

    return reg


def runner_factory(script):
    def runner(case: Case):
        loop = AgentLoop(
            model=MockModel(script=list(script)),
            tools=registry(),
            verifier=Deterministic(lambda s: bool(s.artefact), "produced an answer"),
            guardrails=Guardrails(max_iterations=10, no_progress_after=999),
        )
        return loop.run(case.goal)

    return runner


class TestEvalReport(unittest.TestCase):
    def test_small_eval_sets_announce_their_own_uselessness(self):
        cases = [Case(id=f"c{i}", goal="answer") for i in range(20)]
        report = run_eval(cases, runner_factory([say("the answer")]))
        # ~22 points at n=20: a 10% improvement is indistinguishable from noise.
        self.assertGreater(report.detectable_delta, 0.20)
        self.assertIn("TOO SMALL", report.render())

    def test_a_larger_set_can_detect_smaller_changes(self):
        cases = [Case(id=f"c{i}", goal="answer") for i in range(400)]
        report = run_eval(cases, runner_factory([say("the answer")]))
        self.assertLess(report.detectable_delta, 0.06)
        self.assertNotIn("TOO SMALL", report.render())

    def test_dimensions_are_scored_separately_so_the_report_is_diagnostic(self):
        cases = [Case(id="c1", goal="answer")]
        report = run_eval(cases, runner_factory([say("done")]))
        self.assertEqual(set(report.by_dimension()), set(TRAJECTORY_DIMENSIONS))

    def test_thrashing_shows_up_as_a_tool_selection_penalty(self):
        thrash = [call("search", q="x"), call("search", q="x"), call("search", q="x"),
                  say("finally an answer")]
        report = run_eval([Case(id="c1", goal="g")], runner_factory(thrash))
        selection = report.by_dimension()["tool_selection"]
        self.assertIsNotNone(selection)
        self.assertLess(selection, 1.0)

    def test_slicing_by_tag_surfaces_where_it_fails(self):
        cases = [
            Case(id="easy1", goal="g", tags=("easy",)),
            Case(id="hard1", goal="g", tags=("hard",), check=lambda o: False),
        ]
        report = run_eval(cases, runner_factory([say("answer")]))
        by_tag = report.by_tag()
        self.assertEqual(by_tag["easy"], 1.0)
        self.assertEqual(by_tag["hard"], 0.0)

    def test_a_crashing_runner_is_recorded_not_propagated(self):
        def boom(case):
            raise RuntimeError("harness exploded")

        report = run_eval([Case(id="c1", goal="g")], boom)
        self.assertEqual(report.pass_rate, 0.0)
        self.assertIn("harness exploded", report.results[0].error)


class TestJudgeCalibration(unittest.TestCase):
    def test_perfect_agreement_is_one(self):
        self.assertAlmostEqual(cohens_kappa([1, 0, 1, 0], [1, 0, 1, 0]), 1.0)

    def test_chance_level_agreement_is_about_zero(self):
        human = [1, 0] * 20
        judge = [1, 1, 0, 0] * 10
        self.assertLess(abs(cohens_kappa(human, judge)), 0.2)

    def test_a_judge_that_always_says_pass_scores_zero_despite_looking_accurate(self):
        """The failure an uncalibrated setup hides: 80% raw agreement, kappa 0."""
        human = [1] * 8 + [0] * 2
        judge = [1] * 10
        raw_agreement = sum(h == j for h, j in zip(human, judge)) / len(human)
        self.assertEqual(raw_agreement, 0.8)
        self.assertAlmostEqual(cohens_kappa(human, judge), 0.0)

    def test_mismatched_lengths_are_rejected(self):
        with self.assertRaises(ValueError):
            cohens_kappa([1, 0], [1])


if __name__ == "__main__":
    unittest.main()
