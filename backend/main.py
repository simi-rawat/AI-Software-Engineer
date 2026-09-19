from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent.graph import app as agent_app
from backend.agent.report import generate_report
from backend.code_intelligence.chunk_pipeline import chunk_repository
from backend.ingestion.pipeline import ingest_repository
from backend.retrieval.vector_store import add_chunks

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class IngestRequest(BaseModel):
    source: str


class InvestigateRequest(BaseModel):
    issue_text: str
    repo_path: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(request: IngestRequest):
    try:
        result = ingest_repository(request.source)
        chunks = chunk_repository(result["files"])
        add_chunks(chunks)
        return {
            "files_indexed": len(result["files"]),
            "chunks_indexed": len(chunks),
            "repo_path": result["repo_path"],
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/investigate")
def investigate(request: InvestigateRequest):
    try:
        initial_state = {
            "issue_text": request.issue_text,
            "repo_path": request.repo_path,
            "evidence": [],
            "hypothesis": "",
            "hypothesis_evidence_ids": [],
            "patch_diff": {},
            "test_code": "",
            "execution_result": {},
            "retries_used": 0,
            "verification_status": "pending",
        }
        final_state = agent_app.invoke(initial_state)
        report_markdown = generate_report(final_state)
        return {
            "report_markdown": report_markdown,
            "verification_status": final_state["verification_status"],
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
