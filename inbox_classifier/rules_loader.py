import os
import logging
from pathlib import Path
import requests

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

GITHUB_RAW_URL = 'https://raw.githubusercontent.com/{repo}/main/rules.md'


def _load_local() -> str:
    """Load rules from local file, creating default if missing."""
    if RULES_FILE.exists():
        return RULES_FILE.read_text().strip()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RULES_FILE.write_text(DEFAULT_RULES)
    return DEFAULT_RULES


def _fetch_from_github(repo: str, token: str) -> str:
    """Fetch rules.md from GitHub repo via raw content URL.

    Returns the file content, or raises on failure.
    """
    url = GITHUB_RAW_URL.format(repo=repo)
    response = requests.get(
        url,
        headers={'Authorization': f'Bearer {token}'},
        timeout=10,
    )
    if response.status_code != 200:
        raise RuntimeError(f"GitHub returned {response.status_code}: {response.text[:100]}")
    return response.text


def _update_cache(content: str) -> None:
    """Write rules content to local cache file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RULES_FILE.write_text(content)


def load_rules() -> str:
    """Load classification rules.

    If RULES_REPO is set, fetches from GitHub and caches locally.
    Falls back to local file on failure or when RULES_REPO is not set.
    """
    rules_repo = os.getenv('RULES_REPO')

    if not rules_repo:
        return _load_local()

    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        logger.warning("RULES_REPO set but GITHUB_TOKEN missing, using local cache")
        return _load_local()

    try:
        content = _fetch_from_github(rules_repo, github_token)
        _update_cache(content)
        logger.info(f"Fetched rules from GitHub ({rules_repo})")
        return content
    except Exception as e:
        logger.warning(f"Failed to fetch rules from GitHub: {e}, using local cache")
        return _load_local()
