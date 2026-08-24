"""Module 5 L2 — tool errors as observations, and result sizing.

Run:  python3 examples/02_tools_and_errors.py
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


from ce import ToolError, ToolRegistry

reg = ToolRegistry()


@reg.register(
    "get_customer",
    "Look up a customer by exact email address. Returns name, plan, and signup date.",
    {"email": {"type": "string", "description": "Full email, e.g. 'john@acme.com'."}},
    required=("email",),
    when_to_use="Use when you have an exact email; use search_customers for fuzzy lookup.",
)
def get_customer(email: str) -> str:
    known = {"john@acme.com": "John Doe, plan=pro, since 2024-03-01"}
    if email not in known:
        raise ToolError(
            f"No customer with email {email!r}.",
            hint="Did you mean 'john@acme.com'? Use search_customers for fuzzy lookup.",
            data={"similar": ["john@acme.com"]},
        )
    return known[email]


@reg.register("dump_orders", "Returns every order ever placed.", {}, max_result_tokens=60)
def dump_orders() -> str:
    return "\n".join(f"order {i}: ${i * 3}" for i in range(2_000))


print("=" * 72)
print("1. A useless error vs. an actionable one")
print("=" * 72)
r = reg.dispatch("c1", "get_customer", {"email": "jon@acme.com"})
print("is_error:", r.is_error)
print(r.content)
print("\nThe agent recovers on its NEXT turn instead of dead-ending.")

print()
print("=" * 72)
print("2. A typo is two problems; report both")
print("=" * 72)
print(reg.dispatch("c2", "get_customer", {"e_mail": "john@acme.com"}).content)
print("\nReporting only 'missing email' makes the agent add email AND keep e_mail.")

print()
print("=" * 72)
print("3. Nothing raises into the loop")
print("=" * 72)
print(reg.dispatch("c3", "nonexistent_tool", {}).content)

print()
print("=" * 72)
print("4. Oversized results are truncated LOUDLY")
print("=" * 72)
r = reg.dispatch("c4", "dump_orders", {})
print(r.content[:200], "...")
print("\nresult tokens:", r.tokens, "(capped)")
print("Silent truncation reads as 'this is the whole result'.")

print()
print("=" * 72)
print("5. What your tool set costs on EVERY turn")
print("=" * 72)
print(f"{len(reg.tools)} tools = {reg.schema_tokens()} tokens of permanent overhead")
