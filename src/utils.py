"""Shared helpers used across the app: config, rubric loading, and small utilities."""

import json
import os
from pathlib import Path

# --- Config (override with environment variables if your setup differs) ---
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

SD_HOST = os.environ.get("SD_HOST", "http://127.0.0.1:7860")

BASE_DIR = Path(__file__).resolve().parent.parent
RUBRIC_PATH = BASE_DIR / "data" / "rubrics" / "sample_questions.json"
OUTPUTS_DIR = BASE_DIR / "outputs"


def load_rubrics(path: Path = RUBRIC_PATH) -> list[dict]:
    """Load the list of sample questions + rubrics from disk."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_rubric_by_id(rubric_id: str, path: Path = RUBRIC_PATH) -> dict | None:
    """Fetch a single rubric entry by its id."""
    for entry in load_rubrics(path):
        if entry["id"] == rubric_id:
            return entry
    return None


def ensure_outputs_dir() -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR
