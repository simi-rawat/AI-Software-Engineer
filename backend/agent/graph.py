from __future__ import annotations

from backend.agent.llm_client import call_gemini_json
from backend.agent.state import AgentState
from backend.agent.tools import search_code
from langgraph.graph import END, StateGraph


def _format_evidence_items(evidence_items: list[dict]) -> str:
    lines: list[str] = []
    for index, item in enumerate(evidence_items, start=1):
        lines.append(
            f"Evidence {index} (evidence_id={item.get('id')}):\n"
            f"file_path: {item.get('metadata', {}).get('file_path')}\n"
            f"qualified_name: {item.get('metadata', {}).get('qualified_name')}\n"
            f"source:\n{item.get('document')}"
        )
    return "\n\n".join(lines)


def investigate_node(state: dict) -> dict:
    evidence = search_code(state["issue_text"], k=5)
    return {"evidence": evidence}


def hypothesize_node(state: dict) -> dict:
    prompt = (
        "You are investigating a software issue. Based on the issue text and the "
        "evidence below, identify the most likely root cause.\n\n"
        f"Issue text:\n{state['issue_text']}\n\n"
        f"Evidence:\n{_format_evidence_items(state['evidence'])}\n\n"
        "Respond with ONLY JSON in this exact shape:\n"
        '{"hypothesis": "<string explaining the likely root cause>", '
        '"hypothesis_evidence_ids": ["<ids of evidence items actually used, from the list above>"]}'
    )
    result = call_gemini_json(prompt)
    return {
        "hypothesis": result["hypothesis"],
        "hypothesis_evidence_ids": result["hypothesis_evidence_ids"],
    }


def patch_node(state: dict) -> dict:
    relevant_evidence = [
        item for item in state["evidence"] if item.get("id") in state["hypothesis_evidence_ids"]
    ]
    evidence_text = "\n\n".join(
        [
            f"file_path: {item.get('metadata', {}).get('file_path')}\n"
            f"source:\n{item.get('document')}"
            for item in relevant_evidence
        ]
    )
    prompt = (
        "You are proposing a code fix for the issue below. Use the hypothesis and "
        "the relevant evidence to determine the smallest correct change.\n\n"
        f"Issue text:\n{state['issue_text']}\n\n"
        f"Hypothesis:\n{state['hypothesis']}\n\n"
        f"Relevant evidence:\n{evidence_text}\n\n"
        "Respond with ONLY JSON in this exact shape:\n"
        '{"target_file": "<file path to modify>", '
        '"original_code": "<exact existing code snippet to replace>", '
        '"new_code": "<replacement code>", '
        '"explanation": "<short reason for this change>"}'
    )
    result = call_gemini_json(prompt)
    return {"patch_diff": result}


def test_generate_node(state: dict) -> dict:
    prompt = (
        "You are writing a pytest test for the issue below. Use the hypothesis and the "
        "proposed patch information to produce a single complete test function.\n\n"
        f"Issue text:\n{state['issue_text']}\n\n"
        f"Hypothesis:\n{state['hypothesis']}\n\n"
        f"Patch information:\n{state['patch_diff']}\n\n"
        "Respond with ONLY JSON in this exact shape:\n"
        '{"test_code": "<a single complete pytest test function as a string, testing the behavior described in the issue>"}'
    )
    result = call_gemini_json(prompt)
    return {"test_code": result["test_code"]}


graph = StateGraph(AgentState)
graph.add_node("investigate", investigate_node)
graph.add_node("hypothesize", hypothesize_node)
graph.add_node("patch", patch_node)
graph.add_node("test_generate", test_generate_node)
graph.set_entry_point("investigate")
graph.add_edge("investigate", "hypothesize")
graph.add_edge("hypothesize", "patch")
graph.add_edge("patch", "test_generate")
graph.add_edge("test_generate", END)
app = graph.compile()
