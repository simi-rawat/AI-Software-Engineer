from __future__ import annotations

import json

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
