# References

These are design and conceptual references that informed the project architecture. They are not code copied into this repository.

- **SWE-agent**: informed the idea of a structured tool-based agent loop for software engineering tasks, where the model iteratively gathers context and proposes changes rather than answering in one shot.
- **OpenHands**: informed thinking about action/observation loops for coding agents, especially the idea that an agent should alternate between reasoning and environment feedback.
- **Aider**: informed the choice to use a simple old-code/new-code replacement patch format instead of unified diffs, because it is easier to generate, inspect, and validate programmatically.
- **LangGraph documentation**: used directly as the orchestration library for the agent's state machine, providing the graph-based control flow used by the investigation workflow.
- **SWE-bench**: informed the evaluation framing around root-cause identification and fix verification via test execution, even though this project does not implement the full SWE-bench benchmark.
