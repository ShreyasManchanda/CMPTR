"""Helpers for parsing CrewAI / LLM agent outputs into structured data."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _coerce_text(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, (dict, list)):
        return json.dumps(raw)
    text = getattr(raw, "raw", None)
    if text is None and hasattr(raw, "json_dict"):
        try:
            return json.dumps(raw.json_dict)
        except Exception:
            pass
    if text is None:
        text = str(raw)
    return str(text).strip()


def parse_json_object(raw: Any) -> Optional[dict]:
    """Best-effort parse of an LLM response into a JSON object."""
    if isinstance(raw, dict):
        return raw

    text = _coerce_text(raw)
    if not text:
        return None

    candidates = [text]
    fence = _JSON_BLOCK_RE.search(text)
    if fence:
        candidates.insert(0, fence.group(1).strip())

    # Also try substring from first { to last }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            continue

    logger.warning("Failed to parse agent JSON output")
    return None


def parse_ambiguity_advice(raw: Any) -> dict:
    """
    Normalize ambiguity-agent output.

    On parse failure, fall back to conservative manual_review.
    """
    fallback = {
        "recommended_action": "manual_review",
        "reasoning": "Could not parse ambiguity agent output; defaulting to manual review.",
        "confidence_in_advice": 0.0,
    }
    parsed = parse_json_object(raw)
    if not parsed:
        return fallback

    action = str(parsed.get("recommended_action") or "").strip().lower()
    if action not in {"rescrape", "ignore_outliers", "manual_review"}:
        action = "manual_review"

    try:
        confidence = float(parsed.get("confidence_in_advice", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    reasoning = str(parsed.get("reasoning") or "").strip() or fallback["reasoning"]
    return {
        "recommended_action": action,
        "reasoning": reasoning,
        "confidence_in_advice": confidence,
    }
