import os
import re
import time
from typing import Dict, List, Optional
import requests

from .rules_loader import load_rules

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
# Cheapest current Gemini API model for this lightweight classification task.
# GEMINI_MODEL can still override this default through the service environment.
DEFAULT_MODEL = "gemini-2.5-flash-lite"


def parse_categories(rules: str) -> List[str]:
    """Parse category names from rules text (e.g. IMPORTANT, ROUTINE, OPTIONAL)."""
    return re.findall(r'^(\w+) emails include:', rules, re.MULTILINE)


def classify_email(email: Dict[str, str], api_key: str, model: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Classify email using Google Gemini API.

    Categories are parsed dynamically from rules.md.
    """
    rules = load_rules()
    categories = parse_categories(rules)

    category_list = ', '.join(categories)
    response_format = '\nor\n'.join(f'{c}: [brief reason]' for c in categories)

    prompt = f"""Analyze this email and classify it as {category_list}.

{rules}

Email Details:
Subject: {email['subject']}
From: {email['sender']}
To: {email['to']}
Body: {email['body']}

Respond with EXACTLY this format:
{response_format}
"""

    # Rate limiting: max 1 request per second
    time.sleep(1)

    chosen_model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    url = f"{GEMINI_API_URL}/{chosen_model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 150,
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    }

    # Keep credentials out of URLs, which requests includes in HTTP errors.
    try:
        resp = requests.post(
            url, headers={"x-goog-api-key": api_key}, json=payload, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        # Never propagate request URLs, headers, or response bodies into logs.
        status = getattr(getattr(exc, "response", None), "status_code", None)
        detail = f"HTTP {status}" if status is not None else type(exc).__name__
        raise RuntimeError(f"Gemini request failed ({detail})") from None

    candidates = data.get("candidates", [])
    if not candidates:
        return None

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return None

    response_text = parts[0].get("text", "").strip()

    # Parse response against dynamic categories
    for category in categories:
        if response_text.lower().startswith(f'{category.lower()}:'):
            reasoning = re.sub(f'^{category}:', '', response_text, flags=re.IGNORECASE).strip()
            return {
                'classification': category,
                'reasoning': reasoning
            }

    # No match, return None so caller can skip this email
    return None
