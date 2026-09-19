# Autonomous AI Software Engineer

## Overview
This project is a system that takes a Python repository and a bug or issue description, retrieves relevant code using semantic search, investigates the issue using an LLM agent, proposes a fix, generates a test, executes the fix in a controlled environment, and verifies whether it actually works. The output is an evidence-based engineering report.

It is not a code-generation chatbot. The core differentiator is that fixes are verified by real test execution, not just claimed by the LLM.

## Why this project
This project was built to demonstrate applied AI/ML engineering beyond simply calling an LLM API. It combines retrieval-augmented generation, agentic workflows, and verification-driven design to show how language models can be embedded into a disciplined software engineering loop.

The goal is to keep the model grounded in repository evidence, enforce structured reasoning, and close the loop with executable validation instead of relying on unverified suggestions.

## Architecture
The system follows a pipeline that starts with either a GitHub URL or a local repository path. The repository is cloned or walked, Python files are chunked with the built-in `ast` module, those chunks are embedded locally with `sentence-transformers`, and the vectors are stored in a persistent ChromaDB collection. When an issue description is provided, the agent retrieves relevant code, reasons about the likely root cause, proposes a patch, generates a test, executes the patch in a controlled temporary workspace, and verifies the result. The final output is a markdown engineering report returned through FastAPI endpoints and displayed in a minimal HTML/JavaScript frontend.

Text diagram:

GitHub URL or local path -> ingestion (clone/walk) -> AST-based chunking (`ast` module) -> local embeddings (`sentence-transformers`) -> Chroma vector store -> issue text -> semantic retrieval -> LangGraph agent (`investigate -> hypothesize -> patch -> test_generate -> execute -> verify`, with one automatic retry on failure) -> controlled execution (temp copy + subprocess + pytest) -> markdown engineering report -> FastAPI endpoints -> minimal HTML/JS frontend

## Tech Stack
- Backend: Python, FastAPI
- LLM: Google Gemini (`gemini-3.1-flash-lite`) via `google-genai` SDK
- Embeddings: `sentence-transformers` (`all-MiniLM-L6-v2`), fully local, zero API cost
- Vector DB: ChromaDB (embedded, persistent local storage)
- Agent orchestration: LangGraph
- Code understanding: Python's built-in `ast` module
- Execution: `subprocess` + temporary workspace (not a security sandbox -- see Limitations)
- Frontend: plain HTML/CSS/JavaScript, no framework
- Deployment: Render (backend), static HTML (frontend)

## AI/ML Concepts Demonstrated
Embeddings and semantic search: Code chunks are converted into vectors so that conceptually similar code can be found even when exact keywords do not match. This lets the system retrieve relevant repository context based on meaning rather than only string matching.

RAG: The system retrieves repository evidence first, then passes that context to the LLM so the model reasons over the actual codebase instead of inventing an answer from memory alone.

AST-based code chunking: Python files are parsed with the standard library `ast` module to extract top-level functions, classes, and methods as structured chunks. This preserves code boundaries and gives retrieval more useful units than raw file text alone.

Agentic tool-calling: The LLM can call tools such as semantic search and file reading to gather more evidence while investigating a bug. This turns the model into an active participant in the debugging workflow rather than a passive text generator.

Stateful agent orchestration (LangGraph): The investigation pipeline is modeled as a graph with explicit state transitions across investigation, hypothesis generation, patching, test generation, execution, and verification. This makes the process easier to control, inspect, and extend.

Hallucination mitigation via evidence grounding: The prompts require the model to cite retrieved evidence IDs and operate on concrete code chunks. That keeps the reasoning tied to repository content and reduces unsupported claims.

Verification via test execution: Proposed fixes are not accepted at face value. They are applied to a copied repository and validated by running a generated pytest test against the modified code.

One-retry recovery loop: If the first patch fails, the system feeds the failure output back into the patching step once more. This gives the model a chance to revise the fix using the concrete test result before the run is marked unresolved.

## How to Run Locally
1. Clone the repo.
2. Create a virtual environment and activate it.
3. Run `pip install -r requirements.txt`.
4. Create a `.env` file with `GEMINI_API_KEY=your_key_here`.
5. Run `uvicorn backend.main:app --reload`.
6. Open `frontend/index.html` in a browser, with `API_BASE_URL` set to `http://127.0.0.1:8000`.

## Live Demo
Backend deployed at: https://ai-software-engineer-kfn8.onrender.com

The demo is hosted on Render's free tier, so the first request may be slow due to cold start. See the Limitations section for notes about request timeouts.

## Example Output
A sample engineering report is available at [docs/sample_report.md](docs/sample_report.md).

## Evaluation
The system was tested against three seeded bugs in a controlled test repository (data/seeded_repo): a discount-calculation error, an off-by-one slicing error, and a boundary-condition comparison error. All three were correctly identified, root-caused, patched, tested, and verified via real test execution, with 0/3 requiring the automatic retry (3/3 verified on first attempt).

This is a small, manually verified evaluation appropriate for the project's current scope. Broader benchmark-style evaluation is noted as future work.

## Limitations
- Execution environment is a controlled temporary workspace (isolated directory, subprocess timeout), not a full security sandbox.
- Patch application requires an exact source-code match, not fuzzy patching.
- Scoped to Python repositories only.
- Maximum of one automatic retry before reporting a fix as unresolved.
- All chunks currently share one vector collection; multiple ingested repositories can produce cross-contaminated retrieval results.
- The `/investigate` endpoint is synchronous; combined with the deployed free-tier host's proxy timeout (~30s), multi-step investigations can occasionally time out on the hosted version. This does not occur when run locally.
- Generated code and tests use file-path-based context and are not fully aware of the project's actual Python import structure.

## Future Work
- Asynchronous execution with job polling, which removes the timeout constraint entirely.
- Per-repository vector collections.
- Multi-language support via tree-sitter.
- Real sandboxed execution with Docker or gVisor.
- Broader benchmark-style evaluation inspired by SWE-bench.
- Agentic, multi-call investigation instead of single-pass retrieval.

## Project Structure
- `backend/ingestion/` - repository cloning and local file walking, plus repo ingestion orchestration.
- `backend/code_intelligence/` - AST-based chunk extraction and chunk pipeline wiring.
- `backend/retrieval/` - local embedding generation and Chroma vector store access.
- `backend/agent/` - agent state, tools, reporting, and LangGraph orchestration.
- `backend/execution/` - temporary workspace patch application and pytest execution.
- `backend/main.py` - FastAPI application exposing `/health`, `/ingest`, and `/investigate` endpoints.
- `frontend/` - minimal single-page HTML/CSS/JavaScript interface for repository ingestion and issue investigation.
