"""Tests for compaction and stale tool-result clearing (Module 4, Lesson 4)."""

import unittest

from ce import CompactionPolicy, MockModel, clear_stale_tool_results, compact, say


def trajectory(n_tool_results: int = 10) -> list[dict]:
    msgs = [
        {"role": "system", "content": "you are careful"},
        {"role": "user", "content": "migrate the test suite"},
    ]
    for i in range(n_tool_results):
        msgs.append({"role": "assistant", "content": f"reading file {i}"})
        msgs.append({"role": "tool", "name": "read_file", "content": "x" * 4_000})
    return msgs


class TestStaleToolResults(unittest.TestCase):
    def test_clearing_is_the_cheapest_win_and_needs_no_model(self):
        msgs = trajectory(10)
        before = sum(len(str(m["content"])) for m in msgs)
        cleared = clear_stale_tool_results(msgs, keep_recent=2)
        after = sum(len(str(m["content"])) for m in cleared)
        self.assertLess(after, before * 0.3)

    def test_recent_tool_results_are_kept_verbatim(self):
        cleared = clear_stale_tool_results(trajectory(10), keep_recent=2)
        tool_msgs = [m for m in cleared if m["role"] == "tool"]
        self.assertNotIn("cleared", tool_msgs[-1]["content"])
        self.assertIn("cleared", tool_msgs[0]["content"])

    def test_cleared_results_say_so_rather_than_vanishing(self):
        """Silent removal reads as 'this never happened' to the agent."""
        cleared = clear_stale_tool_results(trajectory(4), keep_recent=1)
        first_tool = next(m for m in cleared if m["role"] == "tool")
        self.assertIn("read_file", first_tool["content"])
        self.assertIn("tokens", first_tool["content"])


class TestCompactionPolicy(unittest.TestCase):
    def test_threshold_is_computed_from_the_effective_window(self):
        policy = CompactionPolicy(nominal_window=200_000, effective_fraction=0.65, trigger_at=0.70)
        self.assertEqual(policy.threshold_tokens, 91_000)
        self.assertFalse(policy.should_compact(90_000))
        self.assertTrue(policy.should_compact(91_000))

    def test_compacting_at_the_nominal_window_would_fire_far_too_late(self):
        effective = CompactionPolicy(nominal_window=200_000)
        naive = CompactionPolicy(nominal_window=200_000, effective_fraction=1.0, trigger_at=0.95)
        self.assertLess(effective.threshold_tokens, naive.threshold_tokens * 0.5)


class TestCompaction(unittest.TestCase):
    def test_head_and_tail_survive_the_summary(self):
        model = MockModel(policy=lambda t, m: say("SUMMARY: read 10 files, none migrated yet."))
        msgs = trajectory(10)
        result = compact(msgs, model=model, policy=CompactionPolicy(keep_head=2, keep_recent=4))
        self.assertEqual(result.messages[0], msgs[0])
        self.assertEqual(result.messages[1], msgs[1])
        self.assertEqual(result.messages[-4:], msgs[-4:])
        self.assertIn("prior_work", result.messages[2]["content"])

    def test_compaction_actually_reduces_tokens(self):
        model = MockModel(policy=lambda t, m: say("SUMMARY: short."))
        result = compact(trajectory(10), model=model, policy=CompactionPolicy())
        self.assertLess(result.ratio, 0.5)

    def test_the_prompt_demands_dead_ends_be_preserved(self):
        """Item 4 is the one people omit, and omitting it makes agents retry."""
        from ce.compaction import COMPACTION_PROMPT

        self.assertIn("Dead ends", COMPACTION_PROMPT)
        self.assertIn("EXACTLY", COMPACTION_PROMPT)  # exact identifiers

    def test_a_short_trajectory_is_left_alone(self):
        model = MockModel(policy=lambda t, m: say("should not be called"))
        msgs = trajectory(1)[:3]
        result = compact(msgs, model=model, policy=CompactionPolicy(keep_head=2, keep_recent=4))
        self.assertEqual(result.compacted_turns, 0)
        self.assertEqual(result.messages, list(msgs))


if __name__ == "__main__":
    unittest.main()
