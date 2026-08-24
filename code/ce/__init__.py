"""ce — a small, dependency-free reference harness for the Context Engineering course.

Every module here implements something the course claims, in a form you can run
and a form the tests can falsify. Nothing requires an API key: `MockModel` makes
the whole package executable offline, which is the only way a harness gets tested.

Quick start:

    from ce import AgentLoop, ToolRegistry, MockModel, Deterministic, say, call

See `code/examples/` for runnable walkthroughs and `code/tests/` for the
guardrail tests — those tests are the course's claims, made falsifiable.
"""

from .compaction import CompactionPolicy, clear_stale_tool_results, compact
from .context import (
    AssembledContext,
    Budget,
    CacheOrderError,
    ContextAssembler,
    Section,
    Stability,
    edge_load,
)
from .evals import Case, EvalReport, cohens_kappa, run_eval, score_trajectory
from .loop import AgentLoop, AgentState, Guardrails, Outcome
from .model import MockModel, Model, ModelResponse, ToolCall, call, say
from .tools import Tool, ToolError, ToolRegistry, ToolResult
from .trace import Trace
from .verify import All, Deterministic, JudgeModel, NeverTrustSelfReport, Tier, Verdict
from .workspace import Workspace

__all__ = [
    "AgentLoop", "AgentState", "All", "AssembledContext", "Budget", "CacheOrderError",
    "Case", "CompactionPolicy", "ContextAssembler", "Deterministic", "EvalReport",
    "Guardrails", "JudgeModel", "MockModel", "Model", "ModelResponse",
    "NeverTrustSelfReport", "Outcome", "Section", "Stability", "Tier", "Tool",
    "ToolCall", "ToolError", "ToolRegistry", "ToolResult", "Trace", "Verdict",
    "Workspace", "call", "clear_stale_tool_results", "cohens_kappa", "compact",
    "edge_load", "run_eval", "say", "score_trajectory",
]
