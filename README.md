# **Context Engineering for AI — Course Outline**

Welcome to the course on Context Engineering for AI. It covers the principles, techniques, and practices for building robust, reliable, and efficient AI systems — from a single well-designed prompt to autonomous agents running unattended.

**2026 edition.** The field reorganized substantially between 2023 and 2026. This edition follows that reorganization: it teaches four nested disciplines — **prompt → context → harness → loop** — and ends with a unifying architecture for agentic systems. See [CHANGELOG.md](./CHANGELOG.md) for what changed from the previous edition.

---

### **Course Structure**

Eight modules. Modules 1–4 build the foundation; 5–6 make systems that act and that you can trust; 7–8 cover the frontier and the architecture that ties it together.

*   [**Module 1: Foundations of Context Engineering**](./Lessons/Module1/)
    *   [Lesson 1: What is Context and Why is it Critical?](./Lessons/Module1/Lesson1_What_is_Context.md)
    *   [Lesson 2: The Evolution and Economics of Context](./Lessons/Module1/Lesson2_Evolution_and_Economics.md)
    *   [Lesson 3: Core Principles of Effective Context Design](./Lessons/Module1/Lesson3_Core_Principles.md)
    *   [Lesson 4: The Four Disciplines — A Map of the Field](./Lessons/Module1/Lesson4_The_Four_Disciplines.md)

*   [**Module 2: Advanced Prompting Techniques**](./Lessons/Module2/)
    *   [Lesson 1: The Anatomy of an Advanced Prompt](./Lessons/Module2/Lesson1_Anatomy_of_an_Advanced_Prompt.md)
    *   [Lesson 2: Foundational Prompting Techniques](./Lessons/Module2/Lesson2_Foundational_Prompting_Techniques.md)
    *   [Lesson 3: Advanced Prompting Strategies](./Lessons/Module2/Lesson3_Advanced_Prompting_Strategies.md)

*   [**Module 3: Retrieval-Augmented Generation (RAG)**](./Lessons/Module3/)
    *   [Lesson 1: Introduction to Retrieval-Augmented Generation](./Lessons/Module3/Lesson1_Introduction_to_RAG.md)
    *   [Lesson 2: Building and Managing the Knowledge Base](./Lessons/Module3/Lesson2_Building_and_Managing_the_Knowledge_Base.md)
    *   [Lesson 3: The Retrieval Process](./Lessons/Module3/Lesson3_The_Retrieval_Process.md)
    *   [Lesson 4: The Generation and Synthesis Process](./Lessons/Module3/Lesson4_The_Generation_and_Synthesis_Process.md)
    *   [Lesson 5: Agentic Retrieval and the Limits of Vector RAG](./Lessons/Module3/Lesson5_Agentic_Retrieval.md)

*   [**Module 4: Optimizing the Context Window**](./Lessons/Module4/)
    *   [Lesson 1: Mastering the Context Window](./Lessons/Module4/Lesson1_Mastering_the_Context_Window.md)
    *   [Lesson 2: Contextual Compression and Distillation](./Lessons/Module4/Lesson2_Contextual_Compression_and_Distillation.md)
    *   [Lesson 3: Re-ranking for Relevance](./Lessons/Module4/Lesson3_Re-ranking_for_Relevance.md)
    *   [Lesson 4: Context Engineering for Long-Horizon Agents](./Lessons/Module4/Lesson4_Long_Horizon_Context.md)

*   [**Module 5: From RAG to Agents**](./Lessons/Module5/)
    *   [Lesson 1: The Rise of AI Agents](./Lessons/Module5/Lesson1_The_Rise_of_AI_Agents.md)
    *   [Lesson 2: Designing and Integrating Tools](./Lessons/Module5/Lesson2_Designing_and_Integrating_Tools.md)
    *   [Lesson 3: Agentic Frameworks and Architectures](./Lessons/Module5/Lesson3_Agentic_Frameworks_and_Architectures.md)
    *   [Lesson 4: MCP and Agent Skills — Packaging Capability](./Lessons/Module5/Lesson4_MCP_and_Agent_Skills.md)

*   [**Module 6: Evaluation, Testing, and Security**](./Lessons/Module6/)
    *   [Lesson 1: Evaluating Context Quality and Agent Performance](./Lessons/Module6/Lesson1_Evaluating_Context_Quality_and_RAG_Performance.md)
    *   [Lesson 2: Testing, Tracing, and Debugging](./Lessons/Module6/Lesson2_Testing_Tracing_and_Debugging.md)
    *   [Lesson 3: Security for Agentic Systems](./Lessons/Module6/Lesson3_Security_for_Context-Aware_Systems.md)

*   [**Module 7: The Frontier**](./Lessons/Module7/)
    *   [Lesson 1: Multi-modal and Computer-Using Agents](./Lessons/Module7/Lesson1_Multi-modal_Context.md)
    *   [Lesson 2: The Evolving Landscape](./Lessons/Module7/Lesson2_The_Evolving_Landscape.md)
    *   [Lesson 3: The Business and Ethics of Agentic AI](./Lessons/Module7/Lesson3_The_Business_and_Ethics_of_Context.md)

*   [**Module 8: Agentic Engineering**](./Lessons/Module8/)
    *   [Lesson 1: The Harness — Where Agents Actually Succeed or Fail](./Lessons/Module8/Lesson1_The_Agent_Harness.md)
    *   [Lesson 2: Loop Engineering](./Lessons/Module8/Lesson2_Loop_Engineering.md)
    *   [Lesson 3: Structuring AI Teams](./Lessons/Module8/Lesson3_Structuring_AI_Teams.md)
    *   [Lesson 4: A Unifying Blueprint — Agentic Architecture](./Lessons/Module8/Lesson4_Agentic_Architecture.md)

---

### **Runnable Code**

The course ships a small, **dependency-free reference harness** in [`code/`](./code/) — standard library only, no API key, no install.

```bash
cd code
python3 -m unittest discover -s tests -t .    # 57 tests
python3 examples/03_agent_loop.py             # the same model under two harnesses
```

Its test suite is the course's argument in falsifiable form. Each guardrail claim has a test that fails if the guardrail is removed — that a loop must not exit on self-report, that tool errors must never raise, that injection cannot amplify absent capability, that a 20-case eval set cannot detect a 10% change. See [`code/README.md`](./code/README.md), including its honest limitations.

---

### **Also in This Repository**

| File | What it's for |
| :--- | :--- |
| [**CHEATSHEET.md**](./CHEATSHEET.md) | Every decision the course asks you to make, on one page. Start here when building |
| [**ANTI_PATTERNS.md**](./ANTI_PATTERNS.md) | Diagnostic reference organized by **symptom** — what you're seeing, what's causing it, and the fix people try first that doesn't work |
| [**INDEX.md**](./INDEX.md) | Concept → lesson → implementation |
| [**templates/**](./templates/) | The architecture spec, eval set, red-team cases, tool spec, compaction prompt, and AGENTS.md skeleton |
| [**FINAL_PROJECT.md**](./FINAL_PROJECT.md) | Build, measure, and attack a complete agentic system |
| [**GLOSSARY.md**](./GLOSSARY.md) | Definitions, including superseded terms marked *(historical)* |
| [**REFERENCES.md**](./REFERENCES.md) | Primary sources, with a note on which figures to trust |
| [**CHANGELOG.md**](./CHANGELOG.md) | What changed in this edition, and why |
| `SOLUTIONS.md` in each module | Worked answers to the hands-on tasks |

---

### **Prerequisites**

*   **Python**, read and write. Code examples are Python; the reference harness needs 3.10+.
*   **Comfort with an API client** — HTTP requests, JSON, environment variables.
*   **No ML background required.** Nothing here involves training a model.
*   **Helpful but not assumed:** having built something with an LLM API and watched it behave badly in production. If you have, several lessons will land as recognition rather than instruction.

### **How to Use This Course**

Roughly **28–35 hours** including the hands-on tasks. Each module README states its own estimate, its learning outcomes, and a short **Check yourself** set.

Work the modules in order; each builds on the last. **Do the hands-on tasks before reading the solutions** — many are designed so the intuitive answer is the wrong one, and discovering that yourself is the point.

**Three paths through it:**

| If you are… | Read |
| :--- | :--- |
| **Building something now** | [CHEATSHEET.md](./CHEATSHEET.md) → [M1 L4](./Lessons/Module1/Lesson4_The_Four_Disciplines.md) → [M8 L4](./Lessons/Module8/Lesson4_Agentic_Architecture.md) → fill in [`templates/architecture-spec.md`](./templates/architecture-spec.md) → return to the modules your thinnest planes need |
| **Debugging something broken** | [ANTI_PATTERNS.md](./ANTI_PATTERNS.md), by symptom |
| **Learning the field properly** | Modules 1→8 in order, hands-on tasks included, then the [Final Project](./FINAL_PROJECT.md) |

If you read only two lessons: [Module 1, Lesson 4](./Lessons/Module1/Lesson4_The_Four_Disciplines.md) is the map, and [Module 8, Lesson 4](./Lessons/Module8/Lesson4_Agentic_Architecture.md) is the destination.

### **Four Things That Won't Change**

Techniques churn; frameworks churn faster. These have held across every model generation so far, and they are what the rest of the course implements:

1.  **Context is finite and degrades.** Every technique in Modules 3 and 4 exists because of this.
2.  **Verification must live outside the agent.** A system that grades its own homework will pass.
3.  **Capability must be scoped.** What an agent *can* do bounds what can go wrong — including what an attacker can make it do.
4.  **You can't improve what you can't measure.** Without evals, every change is a guess with a confident narrator.
