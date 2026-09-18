from typing import TypedDict


class AgentState(TypedDict):
    issue_text: str
    repo_path: str
    evidence: list[dict]
    hypothesis: str
    hypothesis_evidence_ids: list[str]
    patch_diff: str
    test_code: str
    execution_result: dict
    retries_used: int
    verification_status: str
