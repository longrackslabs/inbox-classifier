import re
from anthropic import Anthropic
from typing import Dict, List
import time

from .rules_loader import load_rules


def parse_categories(rules: str) -> List[str]:
    """Parse category names from rules text (e.g. IMPORTANT, ROUTINE, OPTIONAL)."""
    return re.findall(r'^(\w+) emails include:', rules, re.MULTILINE)


def classify_email(email: Dict[str, str], api_key: str) -> Dict[str, str]:
    """Classify email using Claude API.

    Categories are parsed dynamically from rules.md.
    """
    client = Anthropic(api_key=api_key)
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

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=150,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    # Parse response against dynamic categories
    for category in categories:
        if response_text.startswith(f'{category}:'):
            return {
                'classification': category,
                'reasoning': response_text.replace(f'{category}:', '').strip()
            }

    # No match — return None so caller can skip this email
    return None
