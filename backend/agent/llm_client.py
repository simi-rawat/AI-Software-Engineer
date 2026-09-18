from __future__ import annotations

import json

from backend.agent.tools import read_file, search_code
from backend.config import GEMINI_API_KEY
from google import genai
from google.genai.types import GenerateContentConfig


COMPLETION_INSTRUCTION = (
    "You must respond with ONLY valid JSON. Do not include markdown code fences, "
    "explanations, or any text outside the JSON object."
)


def _strip_json_fences(text: str) -> str:
    cleaned_text = text.strip()
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[len("```json"):].strip()
    elif cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[len("```"):].strip()

    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3].strip()

    return cleaned_text


def _parse_response_text(response_text: str) -> dict:
    cleaned_text = _strip_json_fences(response_text)
    return json.loads(cleaned_text)


def call_gemini_json(prompt: str, system_instruction: str = "") -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)
    combined_instruction = f"{system_instruction} {COMPLETION_INSTRUCTION}".strip()

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config=GenerateContentConfig(system_instruction=combined_instruction),
    )

    response_text = response.text.strip()
    try:
        return _parse_response_text(response_text)
    except Exception:
        retry_instruction = (
            f"{combined_instruction} Your previous response could not be parsed as JSON. "
            "Respond with ONLY a valid JSON object and nothing else."
        ).strip()
        retry_response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=GenerateContentConfig(system_instruction=retry_instruction),
        )
        retry_text = retry_response.text.strip()
        try:
            return _parse_response_text(retry_text)
        except Exception as error:
            raise RuntimeError(
                f"Failed to parse Gemini JSON response. Raw text: {retry_text}"
            ) from error


def investigate_issue(issue_text: str, repo_path: str) -> dict:
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    def read_file_tool(relative_path: str) -> str:
        """Read the full contents of a specific file in the repository.

        Use this when a code chunk alone does not give enough context and you need to
        inspect the complete file.

        Args:
            relative_path: Path to the file relative to the repository root.
        """
        return read_file(relative_path, repo_path)

    tool_callables = {
        "search_code": search_code,
        "read_file_tool": read_file_tool,
    }

    chat = client.chats.create(
        model="gemini-3.1-flash-lite",
        config=GenerateContentConfig(tools=[search_code, read_file_tool]),
    )

    prompt = (
        "You are investigating a software issue. Use the available search_code and "
        "read_file tools as needed to gather evidence about what code might be related "
        "to this issue. Here is the issue text:\n\n"
        f"{issue_text}\n\n"
        "Once you have gathered enough evidence, respond with ONLY a valid JSON object "
        "with exactly two keys: \"evidence_summary\" (a string explaining what you found "
        "and why it's relevant) and \"chunks_examined\" (a list of strings naming the "
        "file/function combinations you looked at, e.g. \"repo_cloner.py::clone_repo\")."
    )

    response = chat.send_message(prompt)

    for _ in range(5):
        candidates = getattr(response, "candidates", None) or []
        parts = []
        if candidates:
            content = getattr(candidates[0], "content", None)
            parts = getattr(content, "parts", None) or []

        function_call_parts = [
            part for part in parts if getattr(part, "function_call", None) is not None
        ]
        if not function_call_parts:
            break

        function_response_parts = []
        for fc_part in function_call_parts:
            function_call = fc_part.function_call
            tool = tool_callables.get(function_call.name)
            if tool is None:
                tool_result = f"Error: unknown tool {function_call.name}"
            else:
                try:
                    tool_result = tool(**dict(function_call.args))
                except Exception as error:
                    tool_result = f"Error: {error}"

            function_response_parts.append(
                types.Part.from_function_response(
                    name=function_call.name,
                    response={"result": tool_result},
                )
            )

        response = chat.send_message(function_response_parts)

    if response.text is None:
        raise RuntimeError(
            "Investigation did not complete within the maximum number of tool-calling iterations."
        )

    response_text = response.text.strip()
    try:
        return json.loads(_strip_json_fences(response_text))
    except Exception as error:
        raise RuntimeError(
            f"Failed to parse Gemini investigation response. Raw text: {response_text}"
        ) from error
