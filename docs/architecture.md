# Architecture

This document is a more technical companion to the main README architecture summary. It explains the internal state model, control flow, retrieval schema, and the design boundary between model-driven reasoning and system-controlled execution.

## AgentState
The LangGraph workflow passes a shared `AgentState` object through the nodes. Its fields are:

- `issue_text`: The user-provided bug description or issue report that anchors the investigation.
- `repo_path`: The repository root used for ingestion, retrieval, and later controlled execution.
- `evidence`: The list of retrieved code chunks returned from semantic search; each item includes chunk metadata and source text.
- `hypothesis`: The model's current root-cause explanation for the issue.
- `hypothesis_evidence_ids`: The identifiers of the retrieved evidence items the model actually used to support the hypothesis.
- `patch_diff`: The proposed fix payload, including the target file, original code snippet, replacement code, and explanation.
- `test_code`: The generated pytest test function used to verify the proposed fix.
- `execution_result`: The result of applying the patch and running the generated test in the controlled workspace.
- `retries_used`: The number of automatic retry attempts already consumed after a failed execution.
- `verification_status`: The current verification outcome of the workflow, such as `pending`, `verified`, or `unresolved`.

## LangGraph Flow
The agent is wired as a stateful graph rather than a single monolithic prompt. The node sequence is:

`investigate -> hypothesize -> patch -> test_generate -> execute -> verify`

The conditional routing after `verify` is:

- pass -> `END`
- fail with `retries_used < 1` -> back to `patch`
- fail with `retries_used >= 1` -> `END`

This gives the system one recovery opportunity after a failed test run while still ensuring that unresolved cases terminate cleanly.

## Tool Boundary
The design intentionally separates LLM-decided actions from system-controlled actions.

- LLM-decided tools: `search_code` and `read_file`
- System-controlled actions: patch application and test execution

That boundary is deliberate. The model may choose what evidence to inspect and what files to open, but the actual mutation of code and the execution of tests are performed by deterministic host code. This keeps the agent flexible for investigation while constraining the risky parts of the workflow to code that can be audited, validated, and time-limited.

## Chroma Metadata Schema
Each stored code chunk uses a small metadata record so retrieval can return both semantic similarity and code context.

The chunk metadata schema is:

- `file_path`: Repository-relative path of the source file
- `qualified_name`: Fully qualified symbol name, such as `ClassName.method_name` or a top-level function name
- `symbol_type`: The kind of symbol represented by the chunk (`function`, `class`, or `method`)
- `start_line`: Starting line number of the extracted source span
- `end_line`: Ending line number of the extracted source span

This metadata makes it possible to explain retrieved evidence, identify the symbol being discussed, and build follow-up prompts that point at exact source locations.

## Why AST Chunking
The project uses Python's built-in `ast` module instead of fixed-size text chunking because AST extraction preserves semantic code units. A function or class becomes one coherent chunk of meaning, which is much better for retrieval than arbitrary character- or token-based splits that can break a function across chunk boundaries.

Fixed-size text chunking can split imports from the code they support, cut a function in half, or mingle unrelated statements from different symbols. AST chunking avoids those problems for Python repositories by aligning retrieval units with the language's actual structural boundaries.
