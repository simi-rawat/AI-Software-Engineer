from __future__ import annotations


def _safe_get(mapping: dict | None, key: str, default: str = "N/A") -> str:
    if not isinstance(mapping, dict):
        return default
    value = mapping.get(key)
    if value in (None, "", []):
        return default
    return str(value)


def generate_report(final_state: dict) -> str:
    issue_text = _safe_get(final_state, "issue_text")
    evidence = final_state.get("evidence") if isinstance(final_state, dict) else []
    hypothesis = _safe_get(final_state, "hypothesis")
    hypothesis_evidence_ids = final_state.get("hypothesis_evidence_ids") if isinstance(final_state, dict) else []
    patch_diff = final_state.get("patch_diff") if isinstance(final_state, dict) else {}
    test_code = _safe_get(final_state, "test_code")
    execution_result = final_state.get("execution_result") if isinstance(final_state, dict) else {}
    verification_status = _safe_get(final_state, "verification_status")
    retries_used = final_state.get("retries_used", "N/A") if isinstance(final_state, dict) else "N/A"

    lines: list[str] = []
    lines.append("# Engineering Report")

    lines.append("## Issue")
    lines.append(issue_text)
    lines.append("")

    lines.append("## Evidence Retrieved")
    if isinstance(evidence, list) and evidence:
        for item in evidence:
            metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
            file_path = metadata.get("file_path", "N/A") if isinstance(metadata, dict) else "N/A"
            qualified_name = metadata.get("qualified_name", "N/A") if isinstance(metadata, dict) else "N/A"
            distance = item.get("distance", "N/A") if isinstance(item, dict) else "N/A"
            if isinstance(distance, (int, float)):
                distance_text = f"{distance:.2f}"
            else:
                distance_text = str(distance)
            lines.append(f"- `{file_path}::{qualified_name}` (distance: {distance_text})")
    else:
        lines.append("N/A")
    lines.append("")

    lines.append("## Root Cause Hypothesis")
    lines.append(hypothesis)
    cited_ids = ", ".join(str(item) for item in hypothesis_evidence_ids) if hypothesis_evidence_ids else "N/A"
    lines.append(f"Cited evidence IDs: {cited_ids}")
    lines.append("")

    lines.append("## Proposed Fix")
    target_file = _safe_get(patch_diff, "target_file")
    explanation = _safe_get(patch_diff, "explanation")
    original_code = _safe_get(patch_diff, "original_code")
    new_code = _safe_get(patch_diff, "new_code")
    lines.append(f"### {target_file}")
    lines.append(explanation)
    lines.append("")
    lines.append("```python")
    lines.append("OLD:")
    lines.append(original_code)
    lines.append("NEW:")
    lines.append(new_code)
    lines.append("```")
    lines.append("")

    lines.append("## Generated Test")
    lines.append("```python")
    lines.append(test_code)
    lines.append("```")
    lines.append("")

    lines.append("## Execution Result")
    applied = execution_result.get("applied") if isinstance(execution_result, dict) else None
    passed = execution_result.get("passed") if isinstance(execution_result, dict) else None
    reason = execution_result.get("reason") if isinstance(execution_result, dict) else None
    stdout = execution_result.get("stdout") if isinstance(execution_result, dict) else ""
    stderr = execution_result.get("stderr") if isinstance(execution_result, dict) else ""
    lines.append(f"Applied: {applied if applied is not None else 'N/A'}")
    lines.append(f"Passed: {passed if passed is not None else 'N/A'}")
    if reason not in (None, ""):
        lines.append(f"Reason: {reason}")
    if stdout not in (None, ""):
        lines.append("stdout:")
        lines.append("```text")
        lines.append(str(stdout))
        lines.append("```")
    if stderr not in (None, ""):
        lines.append("stderr:")
        lines.append("```text")
        lines.append(str(stderr))
        lines.append("```")
    lines.append("")

    lines.append("## Verification Status")
    lines.append(f"Status: {str(verification_status).upper()}")
    lines.append(f"Retries used: {retries_used}")
    lines.append("")

    lines.append("## Limitations")
    lines.append(
        "This system's execution environment is a controlled temporary workspace (isolated directory, subprocess timeout), not a full security sandbox. Patch application requires an exact source-code match rather than fuzzy patching. Retrieval and reasoning are scoped to Python repositories only. The system allows a maximum of one automatic retry before reporting a fix as unresolved."
    )

    return "\n".join(lines)
