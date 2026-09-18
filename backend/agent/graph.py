from __future__ import annotations

from backend.agent.llm_client import call_gemini_json
from backend.agent.state import AgentState
from backend.agent.tools import search_code
from backend.execution.executor import apply_patch_and_run_test
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
    prompt_parts = [
        "You are proposing a code fix for the issue below. Use the hypothesis and ",
        "the relevant evidence to determine the smallest correct change.\n\n",
        f"Issue text:\n{state['issue_text']}\n\n",
        f"Hypothesis:\n{state['hypothesis']}\n\n",
        f"Relevant evidence:\n{evidence_text}\n\n",
    ]
    execution_result = state.get("execution_result")
    if execution_result and execution_result.get("passed") is False:
        prompt_parts.extend(
            [
                f"Previous patch diff:\n{state.get('patch_diff')}\n\n",
                f"Previous test code:\n{state.get('test_code')}\n\n",
                "Your previous patch failed this test with the following output: ",
                f"{execution_result.get('stderr') or execution_result.get('stdout')}. ",
                "Revise the patch to fix this.\n\n",
            ]
        )
    prompt_parts.append(
        "Respond with ONLY JSON in this exact shape:\n"
        '{"target_file": "<file path to modify>", '
        '"original_code": "<exact existing code snippet to replace>", '
        '"new_code": "<replacement code>", '
        '"explanation": "<short reason for this change>"}'
    )
    prompt = "".join(prompt_parts)
    result = call_gemini_json(prompt)
    return {"patch_diff": result}


def execute_node(state: dict) -> dict:
    execution_result = apply_patch_and_run_test(
        repo_path=state["repo_path"],
        target_file=state["patch_diff"]["target_file"],
        original_code=state["patch_diff"]["original_code"],
        new_code=state["patch_diff"]["new_code"],
        test_code=state["test_code"],
    )
    return {"execution_result": execution_result}


def verify_node(state: dict) -> dict:
    if state["execution_result"]["passed"] is True:
        return {"verification_status": "verified"}
    if state["retries_used"] < 1:
        return {
            "verification_status": "pending",
            "retries_used": state["retries_used"] + 1,
        }
    return {"verification_status": "unresolved"}


def route_after_verify(state: dict) -> str:
    if state["verification_status"] == "pending":
        return "patch"
    return "end"


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
graph.add_node("execute", execute_node)
graph.add_node("verify", verify_node)
graph.set_entry_point("investigate")
graph.add_edge("investigate", "hypothesize")
graph.add_edge("hypothesize", "patch")
graph.add_edge("patch", "test_generate")
graph.add_edge("test_generate", "execute")
graph.add_edge("execute", "verify")
graph.add_conditional_edges(
    "verify",
    route_after_verify,
    {
        "patch": "patch",
        "end": END,
    },
)
app = graph.compile()
