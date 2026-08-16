"""Image generation module.

Turns the list of missed rubric points into a short text-to-image prompt and
calls a locally running AUTOMATIC1111 (stable-diffusion-webui) instance via
its REST API to generate a simple study diagram.
"""

import base64
import time
from pathlib import Path

import requests

from .utils import SD_HOST, ensure_outputs_dir


def build_image_prompt(missed_points: list[str], topic: str) -> str:
    """Turn missed rubric concepts into a concrete text-to-image prompt."""
    if not missed_points:
        return ""

    concepts = ", ".join(missed_points[:3])  # keep prompt focused, not a wall of text
    return (
        f"simple educational diagram illustrating {topic}, focusing on {concepts}, "
        f"clean labeled infographic style, white background, textbook illustration"
    )


def generate_image(prompt: str, filename_prefix: str = "feedback") -> Path | None:
    """Call the local Stable Diffusion API and save the result to outputs/.
    Returns the saved file path, or None if there was nothing to generate."""

    if not prompt:
        return None

    payload = {
        "prompt": prompt,
        "negative_prompt": "text, watermark, blurry, photorealistic, clutter",
        "steps": 25,
        "width": 512,
        "height": 512,
        "cfg_scale": 7,
    }

    try:
        response = requests.post(f"{SD_HOST}/sdapi/v1/txt2img", json=payload, timeout=300)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not reach Stable Diffusion API at {SD_HOST}. "
            f"Is stable-diffusion-webui running with --api?"
        ) from exc

    data = response.json()
    images = data.get("images", [])
    if not images:
        return None

    image_bytes = base64.b64decode(images[0])
    outputs_dir = ensure_outputs_dir()
    filename = f"{filename_prefix}_{int(time.time())}.png"
    out_path = outputs_dir / filename
    out_path.write_bytes(image_bytes)
    return out_path
