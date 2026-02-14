# Remote Rules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let the service fetch `rules.md` from a private GitHub repo via REST API, with local cache fallback, so rules can be trained from any machine.

**Architecture:** New module `rules_loader.py` replaces the `load_rules()` function currently in `ai_classifier.py`. When `RULES_REPO` env var is set, it fetches from GitHub REST API using `requests`. On failure or when the var is absent, it falls back to the local file at `~/.inbox-classifier/rules.md`. Successful fetches update the local cache.

**Tech Stack:** Python, `requests` library, GitHub REST API

**Design doc:** `docs/plans/2026-02-13-remote-rules-design.md`

---

### Task 1: Add `requests` dependency

**Files:**
- Modify: `pyproject.toml:10-16`

**Step 1: Add requests to dependencies**

In `pyproject.toml`, add `"requests>=2.31.0"` to the `dependencies` list:

```toml
dependencies = [
    "google-api-python-client>=2.150.0",
    "google-auth-httplib2>=0.2.0",
    "google-auth-oauthlib>=1.2.1",
    "anthropic>=0.40.0",
    "python-dotenv>=1.0.1",
    "requests>=2.31.0",
]
```

**Step 2: Install updated dependencies**

Run: `pip install -e .`
Expected: Successfully installs (requests is likely already present as a transitive dep)

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "Add requests dependency for GitHub API access"
```

---

### Task 2: Create `rules_loader.py` — local-only path (TDD)

Extract `load_rules()` from `ai_classifier.py` into its own module, preserving exact current behavior first.

**Files:**
- Create: `inbox_classifier/rules_loader.py`
- Create: `tests/test_rules_loader.py`

**Step 1: Write failing tests for local file loading**

```python
# tests/test_rules_loader.py
from unittest.mock import patch, MagicMock
from inbox_classifier.rules_loader import load_rules

MOCK_RULES = """0_Important emails include:
- Security: password resets
- Personal: real people

1_Routine emails include:
- Monthly statements"""


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.RULES_FILE')
def test_load_rules_local_file(mock_rules_file, mock_getenv):
    """When RULES_REPO not set, reads from local file."""
    mock_getenv.return_value = None  # no RULES_REPO
    mock_rules_file.exists.return_value = True
    mock_rules_file.read_text.return_value = MOCK_RULES

    result = load_rules()

    assert result == MOCK_RULES.strip()
    mock_rules_file.read_text.assert_called_once()


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.RULES_FILE')
@patch('inbox_classifier.rules_loader.CONFIG_DIR')
def test_load_rules_creates_default_when_missing(mock_config_dir, mock_rules_file, mock_getenv):
    """When no RULES_REPO and no local file, creates default."""
    mock_getenv.return_value = None
    mock_rules_file.exists.return_value = False

    result = load_rules()

    assert 'Important emails include:' in result
    mock_config_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_rules_file.write_text.assert_called_once()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_rules_loader.py -v`
Expected: FAIL with ImportError (module doesn't exist yet)

**Step 3: Write minimal implementation**

```python
# inbox_classifier/rules_loader.py
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_rules_loader.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add inbox_classifier/rules_loader.py tests/test_rules_loader.py
git commit -m "Add rules_loader module with local file loading"
```

---

### Task 3: Add GitHub fetch to `rules_loader.py` (TDD)

**Files:**
- Modify: `inbox_classifier/rules_loader.py`
- Modify: `tests/test_rules_loader.py`

**Step 1: Write failing tests for GitHub fetch**

Add these tests to `tests/test_rules_loader.py`:

```python
import requests
from unittest.mock import patch, MagicMock, mock_open


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.requests.get')
@patch('inbox_classifier.rules_loader.RULES_FILE')
@patch('inbox_classifier.rules_loader.CONFIG_DIR')
def test_load_rules_fetches_from_github(mock_config_dir, mock_rules_file, mock_get, mock_getenv):
    """When RULES_REPO is set, fetches from GitHub API."""
    mock_getenv.side_effect = lambda key: {
        'RULES_REPO': 'longrackslabs/inbox-rules',
        'GITHUB_TOKEN': 'ghp_test123',
    }.get(key)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_RULES
    mock_get.return_value = mock_response

    result = load_rules()

    assert result == MOCK_RULES
    mock_get.assert_called_once()
    # Verify it called the right URL
    call_args = mock_get.call_args
    assert 'longrackslabs/inbox-rules' in call_args[0][0]
    assert 'Authorization' in call_args[1]['headers']


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.requests.get')
@patch('inbox_classifier.rules_loader.RULES_FILE')
def test_load_rules_github_updates_cache(mock_rules_file, mock_get, mock_getenv):
    """Successful GitHub fetch updates local cache."""
    mock_getenv.side_effect = lambda key: {
        'RULES_REPO': 'longrackslabs/inbox-rules',
        'GITHUB_TOKEN': 'ghp_test123',
    }.get(key)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_RULES
    mock_get.return_value = mock_response
    mock_rules_file.exists.return_value = True

    load_rules()

    mock_rules_file.write_text.assert_called_once_with(MOCK_RULES)


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.requests.get')
@patch('inbox_classifier.rules_loader.RULES_FILE')
def test_load_rules_github_failure_uses_cache(mock_rules_file, mock_get, mock_getenv):
    """When GitHub fetch fails, falls back to local cache."""
    mock_getenv.side_effect = lambda key: {
        'RULES_REPO': 'longrackslabs/inbox-rules',
        'GITHUB_TOKEN': 'ghp_test123',
    }.get(key)

    mock_get.side_effect = requests.RequestException("Connection failed")
    mock_rules_file.exists.return_value = True
    mock_rules_file.read_text.return_value = MOCK_RULES

    result = load_rules()

    assert result == MOCK_RULES.strip()
    mock_rules_file.read_text.assert_called_once()


@patch('inbox_classifier.rules_loader.os.getenv')
@patch('inbox_classifier.rules_loader.requests.get')
@patch('inbox_classifier.rules_loader.RULES_FILE')
def test_load_rules_github_non_200_uses_cache(mock_rules_file, mock_get, mock_getenv):
    """When GitHub returns non-200, falls back to local cache."""
    mock_getenv.side_effect = lambda key: {
        'RULES_REPO': 'longrackslabs/inbox-rules',
        'GITHUB_TOKEN': 'ghp_test123',
    }.get(key)

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = 'Not Found'
    mock_get.return_value = mock_response
    mock_rules_file.exists.return_value = True
    mock_rules_file.read_text.return_value = MOCK_RULES

    result = load_rules()

    assert result == MOCK_RULES.strip()
```

**Step 2: Run tests to verify the new ones fail**

Run: `pytest tests/test_rules_loader.py -v`
Expected: New GitHub tests FAIL, local tests still PASS

**Step 3: Implement GitHub fetch**

Update `load_rules()` in `inbox_classifier/rules_loader.py`:

```python
import os
import logging
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / '.inbox-classifier'
RULES_FILE = CONFIG_DIR / 'rules.md'

# ... DEFAULT_RULES stays the same ...

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
```

**Step 4: Run all tests**

Run: `pytest tests/test_rules_loader.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add inbox_classifier/rules_loader.py tests/test_rules_loader.py
git commit -m "Add GitHub fetch with local cache fallback to rules_loader"
```

---

### Task 4: Wire `rules_loader` into existing code

Replace `load_rules` usage in `ai_classifier.py` and `main.py` to use the new module.

**Files:**
- Modify: `inbox_classifier/ai_classifier.py:1-8, 33-39, 52-53`
- Modify: `inbox_classifier/main.py:10`
- Modify: `tests/test_ai_classifier.py` (update mock paths)
- Modify: `tests/test_main.py` (update mock paths)

**Step 1: Update `ai_classifier.py`**

Remove `load_rules()`, `CONFIG_DIR`, `RULES_FILE`, `DEFAULT_RULES` from `ai_classifier.py`. Import `load_rules` from `rules_loader` instead.

The file should look like:

```python
import re
from anthropic import Anthropic
from typing import Dict, List
import time

from .rules_loader import load_rules


def parse_categories(rules: str) -> List[str]:
    """Parse category names from rules text (e.g. IMPORTANT, ROUTINE, OPTIONAL)."""
    return re.findall(r'^(\w+) emails include:', rules, re.MULTILINE)


def classify_email(email: Dict[str, str], api_key: str) -> Dict[str, str]:
    # ... rest stays the same ...
```

Note: Remove the `Path` import since it's no longer needed.

**Step 2: Update `main.py` imports**

Change line 10 from:
```python
from .ai_classifier import classify_email, load_rules, parse_categories
```
to:
```python
from .ai_classifier import classify_email, parse_categories
from .rules_loader import load_rules
```

**Step 3: Update test mock paths**

In `tests/test_ai_classifier.py`:
- Change `@patch('inbox_classifier.ai_classifier.load_rules')` to `@patch('inbox_classifier.ai_classifier.load_rules')` — this actually stays the same because `classify_email()` calls `load_rules()` which is now imported from `rules_loader`, so the mock target is the reference in `ai_classifier`'s namespace. **No change needed for existing ai_classifier tests.**

In `tests/test_main.py`:
- Change `@patch('inbox_classifier.main.load_rules')` — this also stays the same for the same reason. The mock targets the name in `main`'s namespace. **No change needed for existing main tests.**

**Step 4: Run all tests**

Run: `pytest tests/ -v`
Expected: ALL PASS (existing tests unchanged, new rules_loader tests pass)

**Step 5: Commit**

```bash
git add inbox_classifier/ai_classifier.py inbox_classifier/main.py
git commit -m "Wire rules_loader into ai_classifier and main"
```

---

### Task 5: Update README and .env documentation

**Files:**
- Modify: `README.md`

**Step 1: Add Remote Rules section to README**

Add a new section after "Customizing Classification Rules":

```markdown
## Remote Rules (Optional)

Store your `rules.md` in a private GitHub repo so you can train the classifier from any machine.

### Setup

1. Create a private repo (e.g., `longrackslabs/inbox-rules`) with your `rules.md` at the root
2. Create a GitHub personal access token with `repo` scope
3. Add to your `.env`:

```
RULES_REPO=longrackslabs/inbox-rules
GITHUB_TOKEN=ghp_your_token_here
```

The service fetches `rules.md` from GitHub each cycle and caches it locally. If GitHub is unreachable, the last cached version is used.

### Training

From any machine with Claude Code and git access to the rules repo:

1. Clone the rules repo: `git clone git@github.com:longrackslabs/inbox-rules.git`
2. Edit `rules.md` using Claude Code training workflow
3. Commit and push — service picks up changes within 60 seconds

If `RULES_REPO` is not set, the service reads from `~/.inbox-classifier/rules.md` (original behavior).
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "Document remote rules setup in README"
```

---

### Task 6: Deploy and verify

**Step 1: Create the private GitHub rules repo**

User creates `longrackslabs/inbox-rules` repo on GitHub with their current `rules.md`.

**Step 2: Set environment variables**

Add `RULES_REPO` and `GITHUB_TOKEN` to the `.env` file.

**Step 3: Restart the service**

```bash
pkill -f inbox-classifier
source .venv/bin/activate && inbox-classifier &
```

**Step 4: Check logs for GitHub fetch**

```bash
tail -20 ~/.inbox-classifier/service.log
```

Expected: `Fetched rules from GitHub (longrackslabs/inbox-rules)` in the log output.

**Step 5: Verify classification still works**

Wait for a poll cycle (60 seconds) and confirm emails are classified as expected.

**Step 6: Test fallback**

Temporarily set `GITHUB_TOKEN` to invalid value, restart, confirm warning in logs and local cache used.

**Step 7: Push feature branch and merge**

```bash
git push
```
