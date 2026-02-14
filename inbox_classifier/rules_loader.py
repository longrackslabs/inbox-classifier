import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / '.inbox-classifier'
RULES_FILE = CONFIG_DIR / 'rules.md'

DEFAULT_RULES = """Important emails include:
- Transactional: receipts, confirmations, invoices, shipping notifications
- Security: password resets, security alerts, 2FA codes
- Personal: real people asking questions, replies in conversations
- Work: emails from colleagues, project-related messages
- Action required: needs response, decision, or follow-up

Routine emails include:
- Monthly statements, account notifications, balance updates
- Automated confirmations that don't need action
- Regular account activity summaries

Optional emails include:
- Promotional: sales, deals, marketing campaigns
- Newsletters: regular updates, digests, subscriptions
- Notifications: social media, app updates, automated alerts
- Bulk: templated content, mass emails

Skip classification for:
- from:example@example.com
- subject:Example subject to skip"""


def _load_local() -> str:
    """Load rules from local file, creating default if missing."""
    if RULES_FILE.exists():
        return RULES_FILE.read_text().strip()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RULES_FILE.write_text(DEFAULT_RULES)
    return DEFAULT_RULES


def load_rules() -> str:
    """Load classification rules.

    If RULES_REPO is set, fetches from GitHub. Otherwise reads local file.
    """
    rules_repo = os.getenv('RULES_REPO')

    if not rules_repo:
        return _load_local()

    # GitHub fetch will be added in Task 3
    return _load_local()
