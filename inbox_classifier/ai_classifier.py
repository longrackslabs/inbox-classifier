from anthropic import Anthropic
from typing import Dict
import time

CLASSIFICATION_PROMPT = """Analyze this email and classify it as IMPORTANT or OPTIONAL.

IMPORTANT emails include:
- Transactional: receipts, confirmations, invoices, shipping notifications
- Security: password resets, security alerts, 2FA codes
- Personal: real people asking questions, replies in conversations
- Work: emails from colleagues, project-related messages
- Action required: needs response, decision, or follow-up

OPTIONAL emails include:
- Promotional: sales, deals, marketing campaigns
- Newsletters: regular updates, digests, subscriptions
- Notifications: social media, app updates, automated alerts
- Bulk: templated content, mass emails

Email Details:
Subject: {subject}
From: {sender}
Body: {body}

Respond with EXACTLY this format:
IMPORTANT: [brief reason]
or
OPTIONAL: [brief reason]
"""

def classify_email(email: Dict[str, str], api_key: str) -> Dict[str, str]:
    """Classify email using Claude API.

    Args:
        email: Dict with keys: subject, sender, body
        api_key: Anthropic API key

    Returns:
        Dict with keys: classification (IMPORTANT/OPTIONAL), reasoning
    """
    client = Anthropic(api_key=api_key)

    prompt = CLASSIFICATION_PROMPT.format(
        subject=email['subject'],
        sender=email['sender'],
        body=email['body']
    )

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

    # Parse response
    if response_text.startswith('IMPORTANT:'):
        classification = 'IMPORTANT'
        reasoning = response_text.replace('IMPORTANT:', '').strip()
    elif response_text.startswith('OPTIONAL:'):
        classification = 'OPTIONAL'
        reasoning = response_text.replace('OPTIONAL:', '').strip()
    else:
        # Default to IMPORTANT if unclear
        classification = 'IMPORTANT'
        reasoning = 'Uncertain - keeping in inbox for safety'

    return {
        'classification': classification,
        'reasoning': reasoning
    }
