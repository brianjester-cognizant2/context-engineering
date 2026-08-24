# Agent: <name>

**Job:** <one sentence — what it accomplishes, for whom>
**Owner:** <the human accountable for this agent's actions>
**Autonomy level:** <1 proposes | 2 sandboxed+approved | 3 autonomous+reviewed | 4 audited>
**Version:** <harness version — bump on any change to tools, prompts, or thresholds>

---

## 1. Model plane

- **Primary model / reasoning effort:**
- **Cheaper model for:** <which steps, and why they don't need frontier reasoning>
- **Cache breakpoints after:** <sections>
- **Pinned version?** <yes/no — if no, say what catches a silent upgrade>

## 2. Context plane

- **Assembly order (stable → volatile):**
  1.
  2.
- **Retrieval strategy:** <query / agentic search / hybrid RAG / none> — **justified by:** <corpus property>
- **Compaction trigger:** <% of *effective* window> — **preserved verbatim:** <goal, dead ends, identifiers…>
- **Durable memory:** <what is written, when, where>
- **Token budget:** <per turn> / <per run> — **enforced where in code:**

## 3. Capability plane

| Tool / skill | Purpose | Permission scope | Destructive? | Error returned to agent |
|---|---|---|---|---|
|  |  |  |  |  |

- **Explicitly NOT given:** <and why — this line is graded>
- **MCP servers connected:** <name, version pinned, credential scope>
- **Tool-set token cost per turn:**

## 4. Control plane

- **Trigger:**
- **Goal (a verifiable end state — if it contains "improve" or "reasonable", rewrite it):**
- **Loop pattern:** <ReAct / plan-and-execute / plan-act-replan / reset loop>
- **Orchestration:** <single / fan-out / pipeline / debate / supervisor / swarm> — **justified by:**
- **Handoff contracts (if multi-agent):** <link or inline>
- **Termination:**
  - iteration cap:
  - token budget:
  - cost ceiling:
  - circuit breaker:
  - no-progress after:
  - **on every non-success exit, a human receives:**

## 5. Verification plane

- **In-loop check:** <tier 1 deterministic / 2 judge / 3 human> — **what exactly is checked:**
- **Offline eval set:** <n cases> — **owner:** — **smallest change it can detect:** ±<x>%
- **Stratified across:** <easy / hard / edge / adversarial / past production failures>
- **Judge rubric + calibration kappa (if tier 2):**
- **Human gates:** <which actions, who approves, what evidence they see>

## 6. Governance plane

- **Traces emitted:** <spans, and the assembled-context log>
- **Cost ceiling per run:** — **what happens at the ceiling:**
- **Untrusted input enters at:** <be honest — this line is graded>
- **Blast radius if fully compromised:**
- **Lethal trifecta present?** <untrusted content + private data + outward action> — if yes, **which leg is removed, or which risk is accepted and by whom:**
- **Kill switch:** <who is authorized, and when was it last tested>

---

## Accepted risks

| Risk | Owner | Mitigation | Review date |
|---|---|---|---|
|  |  |  |  |

## Review questions

1. **Which plane is thinnest?** Deliberate scoping, or an unowned concern?
2. **Trace one plausible failure back to a plane.** Is your fix structural or a wording change?
3. **What evidence would justify promoting one autonomy level?** What would demote it?
