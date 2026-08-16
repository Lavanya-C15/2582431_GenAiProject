"""Grading module.

Sends the student's answer + question + rubric to a local LLM (via Ollama)
and asks it to return structured JSON describing which rubric points were
covered, which were missed, and an overall score.
"""

import json
import re

import requests

from .utils import OLLAMA_HOST, OLLAMA_MODEL

GRADING_PROMPT_TEMPLATE = """You are an exam grader. Compare the STUDENT ANSWER to the QUESTION and the
RUBRIC below. The rubric is a list of key concepts that a complete answer should cover.

QUESTION:
{question}

RUBRIC (key concepts expected in a complete answer):
{rubric_list}

STUDENT ANSWER:
{student_answer}

Decide, for each rubric concept, whether the student's answer covers it (even if worded
differently), or misses it. Then respond with ONLY a JSON object in exactly this shape,
with no extra commentary, no markdown fences, and no text before or after it:

{{
  "score": <number 0-100>,
  "covered_points": ["<concept text>", ...],
  "missed_points": ["<concept text>", ...],
  "summary": "<one or two sentence overall feedback>"
}}
"""


def _build_prompt(question: str, key_points: list[dict], student_answer: str) -> str:
    rubric_list = "\n".join(f"- {kp['concept']}" for kp in key_points)
    return GRADING_PROMPT_TEMPLATE.format(
        question=question, rubric_list=rubric_list, student_answer=student_answer
    )


def _extract_json(raw_text: str) -> dict:
    """LLMs sometimes wrap JSON in prose or markdown fences. Pull out the first
    {...} block and parse it."""
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output:\n{raw_text}")
    return json.loads(match.group(0))


def grade_answer(question: str, key_points: list[dict], student_answer: str,
                  retries: int = 1) -> dict:
    """Call the local LLM and return a dict with score, covered_points,
    missed_points, and summary. Raises RuntimeError if the model can't be
    reached, and ValueError if its output can't be parsed after retries."""

    prompt = _build_prompt(question, key_points, student_answer)

    last_error = None
    for _ in range(retries + 1):
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=120,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {OLLAMA_HOST}. "
                f"Is it running? (ollama serve / ollama run {OLLAMA_MODEL})"
            ) from exc

        raw_text = response.json().get("response", "")
        try:
            result = _extract_json(raw_text)
            result.setdefault("covered_points", [])
            result.setdefault("missed_points", [])
            result.setdefault("summary", "")
            result.setdefault("score", 0)
            return result
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            continue

    raise ValueError(f"Model did not return valid JSON after retries: {last_error}")
