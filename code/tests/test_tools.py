"""Tests for tool dispatch: errors are observations, never exceptions (Module 5 L2)."""

import unittest

from ce import ToolError, ToolRegistry


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()

    @reg.register(
        "get_customer",
        "Look up a customer by email.",
        {"email": {"type": "string", "description": "Full email address."}},
        required=("email",),
        when_to_use="Use when you have an exact email; use search_customers for fuzzy lookup.",
    )
    def get_customer(email: str) -> str:
        if email != "john@acme.com":
            raise ToolError(
                f"No customer with email {email!r}.",
                hint="Did you mean 'john@acme.com'? Use search_customers for fuzzy lookup.",
            )
        return "Customer John, plan=pro"

    @reg.register(
        "explode", "Raises an unexpected internal error.", {}, max_result_tokens=50
    )
    def explode() -> str:
        raise RuntimeError("database connection lost")

    @reg.register(
        "firehose", "Returns far too much data.", {}, max_result_tokens=50
    )
    def firehose() -> str:
        return "row\n" * 5_000

    @reg.register(
        "delete_everything", "Irreversibly deletes all records.", {}, destructive=True
    )
    def delete_everything() -> str:
        return "deleted"

    return reg


class TestDispatchNeverRaises(unittest.TestCase):
    def setUp(self):
        self.reg = build_registry()

    def test_unexpected_exception_becomes_an_observation(self):
        result = self.reg.dispatch("1", "explode", {})
        self.assertTrue(result.is_error)
        self.assertIn("database connection lost", str(result.content))

    def test_unknown_tool_lists_the_available_ones(self):
        result = self.reg.dispatch("1", "no_such_tool", {})
        self.assertTrue(result.is_error)
        self.assertIn("get_customer", str(result.content))

    def test_missing_argument_names_what_is_required(self):
        result = self.reg.dispatch("1", "get_customer", {})
        self.assertTrue(result.is_error)
        self.assertIn("email", str(result.content))

    def test_a_typo_surfaces_both_problems_at_once(self):
        """`e_mail` is simultaneously a missing arg and an unknown one.

        Reporting only the first sends the agent chasing half the problem — it
        adds `email` and keeps sending `e_mail` too.
        """
        result = self.reg.dispatch("1", "get_customer", {"e_mail": "x"})
        self.assertTrue(result.is_error)
        content = str(result.content)
        self.assertIn("missing required argument(s): email", content)
        self.assertIn("unknown argument(s): e_mail", content)


class TestActionableErrors(unittest.TestCase):
    def test_tool_error_hint_reaches_the_agent(self):
        reg = build_registry()
        result = reg.dispatch("1", "get_customer", {"email": "jon@acme.com"})
        self.assertTrue(result.is_error)
        self.assertIn("john@acme.com", str(result.content))
        self.assertIn("Hint:", str(result.content))


class TestResultSizing(unittest.TestCase):
    def test_oversized_results_are_truncated_loudly(self):
        reg = build_registry()
        result = reg.dispatch("1", "firehose", {})
        self.assertIn("TRUNCATED", str(result.content))
        self.assertLess(result.tokens, 400)

    def test_schema_tokens_expose_the_cost_of_the_tool_set(self):
        reg = build_registry()
        self.assertGreater(reg.schema_tokens(), 0)


class TestSchemaIsPromptSurface(unittest.TestCase):
    def test_when_to_use_is_included_in_the_description(self):
        reg = build_registry()
        schema = next(s for s in reg.schemas() if s["name"] == "get_customer")
        self.assertIn("search_customers", schema["description"])


if __name__ == "__main__":
    unittest.main()
