"""Token accounting.

The course is built on the premise that context is a finite, degrading resource
(Module 4, Lesson 1). You cannot budget what you do not measure, so token
counting is the foundation everything else in this package sits on.

The default estimator is deliberately crude — roughly 4 characters per token,
which is close enough for English prose to make budgeting decisions. Swap in a
real tokenizer for production: `set_counter(lambda s: len(enc.encode(s)))`.
"""

from __future__ import annotations

from typing import Callable

_CHARS_PER_TOKEN = 4

_counter: Callable[[str], int] = lambda s: max(1, (len(s) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN)


def set_counter(fn: Callable[[str], int]) -> None:
    """Install a real tokenizer. Called once at startup."""
    global _counter
    _counter = fn


def count(text: str) -> int:
    """Token count for a string."""
    return _counter(text) if text else 0


def count_all(*parts: str) -> int:
    return sum(count(p) for p in parts)
