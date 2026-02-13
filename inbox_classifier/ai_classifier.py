import re
from anthropic import Anthropic
from pathlib import Path
from typing import Dict, List
import time

CONFIG_DIR = Path.home() / '.inbox-classifier'
RULES_FILE = CONFIG_DIR / 'rules.md'

DEFAULT_RULES = """IMPORTANT emails include:
- Transactional: receipts, confirmations, invoices, shipping notifications
- Security: password resets, security alerts, 2FA codes
- Personal: real people asking questions, replies in conversations
- Work: emails from colleagues, project-related messages
- Action required: needs response, decision, or follow-up

ROUTINE emails include:
- Monthly statements, account notifications, balance updates
- Automated confirmations that don't need action
- Regular account activity summaries

OPTIONAL emails include:
- Promotional: sales, deals, marketing campaigns
- Newsletters: regular updates, digests, subscriptions
- Notifications: social media, app updates, automated alerts
- Bulk: templated content, mass emails"""


def load_rules() -> str:
    """Load classification rules from ~/.inbox-classifier/rules.md, creating default if missing."""
    if RULES_FILE.exists():
        return RULES_FILE.read_text().strip()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RULES_FILE.write_text(DEFAULT_RULES)
    return DEFAULT_RULES


def parse_categories(rules: str) -> List[str]:
    """Parse category names from rules text (e.g. IMPORTANT, ROUTINE, OPTIONAL)."""
    return re.findall(r'^([A-Z_]+) emails include:', rules, re.MULTILINE)


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

    # Default to first category if unclear
    return {
        'classification': categories[0],
        'reasoning': 'Uncertain - defaulting to first category for safety'
    }
