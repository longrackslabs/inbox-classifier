# Inbox Classifier Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a background service that monitors Gmail inbox and uses Claude API to classify emails as important or optional, applying labels for review.

**Architecture:** Python service polls Gmail API every 60 seconds for unread emails, sends uncertain ones to Claude API for classification, applies Gmail labels based on results, and logs all decisions to JSONL file.

**Tech Stack:** Python 3.10+, Google Gmail API, Anthropic Python SDK, launchd (macOS)

---

## Task 1: Project Setup

**Files:**
- Create: `inbox-classifier/README.md`
- Create: `inbox-classifier/requirements.txt`
- Create: `inbox-classifier/.gitignore`
- Create: `inbox-classifier/pyproject.toml`

**Step 1: Create project directory**

```bash
mkdir -p inbox-classifier
cd inbox-classifier
```

**Step 2: Create README**

```markdown
# Inbox Classifier

AI-powered Gmail inbox classifier using Claude API.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set up Gmail API credentials (see docs/setup-gmail.md)
3. Set ANTHROPIC_API_KEY environment variable
4. Run: `python -m inbox_classifier.main`

## Architecture

- Polls Gmail every 60 seconds for unread emails
- Classifies emails using Claude API
- Applies labels: Classifier/Important or Classifier/Optional
- Logs all decisions to ~/.inbox-classifier/classifications.jsonl
```

**Step 3: Create requirements.txt**

```txt
google-api-python-client==2.150.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.1
anthropic==0.40.0
python-dotenv==1.0.1
```

**Step 4: Create .gitignore**

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.env
credentials.json
token.json
.DS_Store
*.log
```

**Step 5: Create pyproject.toml**

```toml
[project]
name = "inbox-classifier"
version = "0.1.0"
description = "AI-powered Gmail inbox classifier"
requires-python = ">=3.10"
dependencies = [
    "google-api-python-client>=2.150.0",
    "google-auth-httplib2>=0.2.0",
    "google-auth-oauthlib>=1.2.1",
    "anthropic>=0.40.0",
    "python-dotenv>=1.0.1",
]

[project.scripts]
inbox-classifier = "inbox_classifier.main:main"
```

**Step 6: Commit**

```bash
git add .
git commit -m "Initial project setup with dependencies"
```

---

## Task 2: Gmail API Authentication

**Files:**
- Create: `inbox-classifier/inbox_classifier/__init__.py`
- Create: `inbox-classifier/inbox_classifier/gmail_auth.py`
- Create: `inbox-classifier/tests/test_gmail_auth.py`
- Create: `inbox-classifier/docs/setup-gmail.md`

**Step 1: Create package structure**

```bash
mkdir -p inbox_classifier tests docs
touch inbox_classifier/__init__.py
```

**Step 2: Write Gmail auth test**

File: `tests/test_gmail_auth.py`

```python
import os
from pathlib import Path
from inbox_classifier.gmail_auth import get_gmail_service

def test_gmail_auth_creates_service():
    """Test that Gmail service is created successfully."""
    # This test requires valid credentials
    # Skip in CI, run manually for validation
    if not os.path.exists("credentials.json"):
        import pytest
        pytest.skip("credentials.json not found")

    service = get_gmail_service()
    assert service is not None
    assert hasattr(service, 'users')
```

**Step 3: Run test to verify it fails**

```bash
pytest tests/test_gmail_auth.py -v
```

Expected: ImportError or ModuleNotFoundError

**Step 4: Write Gmail auth implementation**

File: `inbox_classifier/gmail_auth.py`

```python
import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    token_path = Path.home() / '.inbox-classifier' / 'token.json'
    creds_path = Path('credentials.json')

    # Create config directory if needed
    token_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    "credentials.json not found. "
                    "Download from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)
```

**Step 5: Create setup documentation**

File: `docs/setup-gmail.md`

```markdown
# Gmail API Setup

1. Go to https://console.cloud.google.com/
2. Create new project: "Inbox Classifier"
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `credentials.json`
6. Place `credentials.json` in project root
7. Run the service - it will open browser for authentication
8. Token will be saved to `~/.inbox-classifier/token.json`
```

**Step 6: Commit**

```bash
git add inbox_classifier/gmail_auth.py tests/test_gmail_auth.py docs/setup-gmail.md inbox_classifier/__init__.py
git commit -m "Add Gmail API authentication"
```

---

## Task 3: Gmail Label Management

**Files:**
- Create: `inbox-classifier/inbox_classifier/gmail_labels.py`
- Create: `inbox-classifier/tests/test_gmail_labels.py`

**Step 1: Write label management test**

File: `tests/test_gmail_labels.py`

```python
from unittest.mock import Mock, patch
from inbox_classifier.gmail_labels import ensure_labels_exist, get_label_id

def test_ensure_labels_exist_creates_missing_labels():
    """Test that missing labels are created."""
    mock_service = Mock()
    mock_service.users().labels().list().execute.return_value = {
        'labels': []
    }
    mock_service.users().labels().create().execute.return_value = {
        'id': 'Label_123',
        'name': 'Classifier/Important'
    }

    label_ids = ensure_labels_exist(mock_service)

    assert 'important' in label_ids
    assert 'optional' in label_ids
    assert mock_service.users().labels().create.call_count == 2

def test_get_label_id_returns_existing_label():
    """Test getting ID of existing label."""
    mock_service = Mock()
    mock_service.users().labels().list().execute.return_value = {
        'labels': [
            {'id': 'Label_123', 'name': 'Classifier/Important'},
            {'id': 'Label_456', 'name': 'Classifier/Optional'}
        ]
    }

    label_id = get_label_id(mock_service, 'Classifier/Important')

    assert label_id == 'Label_123'
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_gmail_labels.py -v
```

Expected: ImportError

**Step 3: Write label management implementation**

File: `inbox_classifier/gmail_labels.py`

```python
from typing import Dict

LABEL_IMPORTANT = 'Classifier/Important'
LABEL_OPTIONAL = 'Classifier/Optional'

def get_label_id(service, label_name: str) -> str | None:
    """Get label ID by name, return None if not found."""
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    for label in labels:
        if label['name'] == label_name:
            return label['id']

    return None

def create_label(service, label_name: str) -> str:
    """Create a new label and return its ID."""
    label_object = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }

    result = service.users().labels().create(
        userId='me',
        body=label_object
    ).execute()

    return result['id']

def ensure_labels_exist(service) -> Dict[str, str]:
    """Ensure required labels exist, create if missing.

    Returns:
        Dict mapping 'important' and 'optional' to label IDs
    """
    label_ids = {}

    for key, label_name in [('important', LABEL_IMPORTANT),
                            ('optional', LABEL_OPTIONAL)]:
        label_id = get_label_id(service, label_name)
        if label_id is None:
            label_id = create_label(service, label_name)
        label_ids[key] = label_id

    return label_ids
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_gmail_labels.py -v
```

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add inbox_classifier/gmail_labels.py tests/test_gmail_labels.py
git commit -m "Add Gmail label management"
```

---

## Task 4: Email Fetcher

**Files:**
- Create: `inbox-classifier/inbox_classifier/email_fetcher.py`
- Create: `inbox-classifier/tests/test_email_fetcher.py`

**Step 1: Write email fetcher test**

File: `tests/test_email_fetcher.py`

```python
from unittest.mock import Mock
from inbox_classifier.email_fetcher import fetch_unread_emails, get_email_details

def test_fetch_unread_emails_returns_message_ids():
    """Test fetching unread email IDs."""
    mock_service = Mock()
    mock_service.users().messages().list().execute.return_value = {
        'messages': [
            {'id': 'msg1'},
            {'id': 'msg2'}
        ]
    }

    messages = fetch_unread_emails(mock_service)

    assert len(messages) == 2
    assert messages[0]['id'] == 'msg1'

def test_get_email_details_extracts_metadata():
    """Test extracting email subject and sender."""
    mock_service = Mock()
    mock_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Email'},
                {'name': 'From', 'value': 'sender@example.com'}
            ],
            'body': {
                'data': 'VGVzdCBib2R5'  # base64 for "Test body"
            }
        },
        'labelIds': ['INBOX', 'UNREAD']
    }

    details = get_email_details(mock_service, 'msg1')

    assert details['subject'] == 'Test Email'
    assert details['sender'] == 'sender@example.com'
    assert 'Test body' in details['body']
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_email_fetcher.py -v
```

Expected: ImportError

**Step 3: Write email fetcher implementation**

File: `inbox_classifier/email_fetcher.py`

```python
import base64
from typing import List, Dict

def fetch_unread_emails(service, label_ids: List[str] = None) -> List[Dict]:
    """Fetch unread emails from inbox, optionally excluding labeled ones.

    Args:
        service: Gmail API service
        label_ids: List of label IDs to exclude (already classified emails)

    Returns:
        List of message objects with 'id' field
    """
    query = 'is:unread in:inbox'

    # Exclude already classified emails
    if label_ids:
        for label_id in label_ids:
            query += f' -label:{label_id}'

    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=100
    ).execute()

    return results.get('messages', [])

def get_email_details(service, message_id: str) -> Dict[str, str]:
    """Get email subject, sender, and body preview.

    Returns:
        Dict with keys: id, subject, sender, body, label_ids
    """
    message = service.users().messages().get(
        userId='me',
        id=message_id,
        format='full'
    ).execute()

    headers = message['payload'].get('headers', [])
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), '')

    # Extract body (handle both body.data and parts)
    body = ''
    payload = message['payload']

    if 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    elif 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                break

    # Limit body to first 300 characters
    body_preview = body[:300] if body else ''

    return {
        'id': message_id,
        'subject': subject,
        'sender': sender,
        'body': body_preview,
        'label_ids': message.get('labelIds', [])
    }
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_email_fetcher.py -v
```

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add inbox_classifier/email_fetcher.py tests/test_email_fetcher.py
git commit -m "Add email fetching functionality"
```

---

## Task 5: Claude AI Classifier

**Files:**
- Create: `inbox-classifier/inbox_classifier/ai_classifier.py`
- Create: `inbox-classifier/tests/test_ai_classifier.py`
- Create: `inbox-classifier/.env.example`

**Step 1: Write AI classifier test**

File: `tests/test_ai_classifier.py`

```python
from unittest.mock import Mock, patch
from inbox_classifier.ai_classifier import classify_email

def test_classify_email_returns_important():
    """Test classification of important email."""
    with patch('inbox_classifier.ai_classifier.Anthropic') as mock_anthropic:
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text='IMPORTANT: This is a receipt')]
        mock_client.messages.create.return_value = mock_response

        email = {
            'subject': 'Your receipt',
            'sender': 'store@example.com',
            'body': 'Thank you for your purchase'
        }

        result = classify_email(email, 'test-key')

        assert result['classification'] == 'IMPORTANT'
        assert 'receipt' in result['reasoning'].lower()

def test_classify_email_returns_optional():
    """Test classification of optional email."""
    with patch('inbox_classifier.ai_classifier.Anthropic') as mock_anthropic:
        mock_client = Mock()
        mock_anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text='OPTIONAL: This is a newsletter')]
        mock_client.messages.create.return_value = mock_response

        email = {
            'subject': 'Weekly digest',
            'sender': 'newsletter@example.com',
            'body': 'Here are this weeks top stories'
        }

        result = classify_email(email, 'test-key')

        assert result['classification'] == 'OPTIONAL'
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_ai_classifier.py -v
```

Expected: ImportError

**Step 3: Create .env.example**

File: `.env.example`

```
ANTHROPIC_API_KEY=your_api_key_here
```

**Step 4: Write AI classifier implementation**

File: `inbox_classifier/ai_classifier.py`

```python
import anthropic
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
    client = anthropic.Anthropic(api_key=api_key)

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
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_ai_classifier.py -v
```

Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add inbox_classifier/ai_classifier.py tests/test_ai_classifier.py .env.example
git commit -m "Add Claude AI email classifier"
```

---

## Task 6: Email Labeler

**Files:**
- Create: `inbox-classifier/inbox_classifier/email_labeler.py`
- Create: `inbox-classifier/tests/test_email_labeler.py`

**Step 1: Write email labeler test**

File: `tests/test_email_labeler.py`

```python
from unittest.mock import Mock
from inbox_classifier.email_labeler import apply_label

def test_apply_label_adds_label_to_message():
    """Test applying label to email."""
    mock_service = Mock()
    mock_service.users().messages().modify().execute.return_value = {
        'id': 'msg1',
        'labelIds': ['INBOX', 'Label_123']
    }

    result = apply_label(mock_service, 'msg1', 'Label_123')

    assert result['id'] == 'msg1'
    mock_service.users().messages().modify.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_email_labeler.py -v
```

Expected: ImportError

**Step 3: Write email labeler implementation**

File: `inbox_classifier/email_labeler.py`

```python
from typing import Dict

def apply_label(service, message_id: str, label_id: str) -> Dict:
    """Apply label to an email message.

    Args:
        service: Gmail API service
        message_id: Email message ID
        label_id: Label ID to apply

    Returns:
        Modified message object
    """
    result = service.users().messages().modify(
        userId='me',
        id=message_id,
        body={'addLabelIds': [label_id]}
    ).execute()

    return result
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_email_labeler.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add inbox_classifier/email_labeler.py tests/test_email_labeler.py
git commit -m "Add email labeling functionality"
```

---

## Task 7: Classification Logger

**Files:**
- Create: `inbox-classifier/inbox_classifier/logger.py`
- Create: `inbox-classifier/tests/test_logger.py`

**Step 1: Write logger test**

File: `tests/test_logger.py`

```python
import json
from pathlib import Path
from inbox_classifier.logger import ClassificationLogger

def test_logger_writes_to_file(tmp_path):
    """Test that logger writes classifications to JSONL."""
    log_file = tmp_path / "test.jsonl"
    logger = ClassificationLogger(log_file)

    logger.log_classification(
        email_id='msg1',
        subject='Test Subject',
        sender='test@example.com',
        classification='IMPORTANT',
        reasoning='Test reason'
    )

    assert log_file.exists()

    with open(log_file) as f:
        line = f.readline()
        entry = json.loads(line)

        assert entry['email_id'] == 'msg1'
        assert entry['classification'] == 'IMPORTANT'
        assert 'timestamp' in entry

def test_logger_creates_directory(tmp_path):
    """Test that logger creates parent directory."""
    log_file = tmp_path / "subdir" / "test.jsonl"
    logger = ClassificationLogger(log_file)

    logger.log_classification(
        email_id='msg1',
        subject='Test',
        sender='test@example.com',
        classification='OPTIONAL',
        reasoning='Test'
    )

    assert log_file.exists()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_logger.py -v
```

Expected: ImportError

**Step 3: Write logger implementation**

File: `inbox_classifier/logger.py`

```python
import json
from pathlib import Path
from datetime import datetime
from typing import Union

class ClassificationLogger:
    """Logger for email classifications."""

    def __init__(self, log_path: Union[str, Path] = None):
        """Initialize logger.

        Args:
            log_path: Path to JSONL log file. Defaults to ~/.inbox-classifier/classifications.jsonl
        """
        if log_path is None:
            log_path = Path.home() / '.inbox-classifier' / 'classifications.jsonl'

        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_classification(
        self,
        email_id: str,
        subject: str,
        sender: str,
        classification: str,
        reasoning: str
    ):
        """Log a classification decision.

        Args:
            email_id: Gmail message ID
            subject: Email subject
            sender: Email sender
            classification: IMPORTANT or OPTIONAL
            reasoning: Classification reasoning from AI
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'email_id': email_id,
            'subject': subject,
            'sender': sender,
            'classification': classification,
            'reasoning': reasoning
        }

        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_logger.py -v
```

Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add inbox_classifier/logger.py tests/test_logger.py
git commit -m "Add classification logging"
```

---

## Task 8: Main Service Loop

**Files:**
- Create: `inbox-classifier/inbox_classifier/main.py`
- Create: `inbox-classifier/tests/test_main.py`

**Step 1: Write main service test**

File: `tests/test_main.py`

```python
from unittest.mock import Mock, patch
from inbox_classifier.main import process_emails

def test_process_emails_classifies_and_labels():
    """Test that process_emails handles full workflow."""
    mock_service = Mock()
    mock_logger = Mock()
    label_ids = {'important': 'Label_123', 'optional': 'Label_456'}
    api_key = 'test-key'

    # Mock email fetcher
    with patch('inbox_classifier.main.fetch_unread_emails') as mock_fetch:
        with patch('inbox_classifier.main.get_email_details') as mock_details:
            with patch('inbox_classifier.main.classify_email') as mock_classify:
                with patch('inbox_classifier.main.apply_label') as mock_label:

                    mock_fetch.return_value = [{'id': 'msg1'}]
                    mock_details.return_value = {
                        'id': 'msg1',
                        'subject': 'Test',
                        'sender': 'test@example.com',
                        'body': 'Test body',
                        'label_ids': ['INBOX']
                    }
                    mock_classify.return_value = {
                        'classification': 'IMPORTANT',
                        'reasoning': 'Test reason'
                    }

                    count = process_emails(mock_service, label_ids, api_key, mock_logger)

                    assert count == 1
                    mock_label.assert_called_once_with(mock_service, 'msg1', 'Label_123')
                    mock_logger.log_classification.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_main.py -v
```

Expected: ImportError

**Step 3: Write main service implementation**

File: `inbox_classifier/main.py`

```python
import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

from inbox_classifier.gmail_auth import get_gmail_service
from inbox_classifier.gmail_labels import ensure_labels_exist
from inbox_classifier.email_fetcher import fetch_unread_emails, get_email_details
from inbox_classifier.ai_classifier import classify_email
from inbox_classifier.email_labeler import apply_label
from inbox_classifier.logger import ClassificationLogger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_emails(service, label_ids: dict, api_key: str, classification_logger: ClassificationLogger) -> int:
    """Process unread emails and classify them.

    Returns:
        Number of emails processed
    """
    # Fetch unread emails that haven't been classified
    classified_label_ids = list(label_ids.values())
    messages = fetch_unread_emails(service, classified_label_ids)

    if not messages:
        logger.info("No new emails to classify")
        return 0

    logger.info(f"Found {len(messages)} unread emails to classify")

    for message in messages:
        try:
            # Get email details
            email = get_email_details(service, message['id'])

            # Classify using AI
            result = classify_email(email, api_key)
            classification = result['classification']
            reasoning = result['reasoning']

            # Apply appropriate label
            label_id = label_ids['important'] if classification == 'IMPORTANT' else label_ids['optional']
            apply_label(service, email['id'], label_id)

            # Log decision
            classification_logger.log_classification(
                email_id=email['id'],
                subject=email['subject'],
                sender=email['sender'],
                classification=classification,
                reasoning=reasoning
            )

            logger.info(f"Classified '{email['subject'][:50]}' as {classification}")

        except Exception as e:
            logger.error(f"Error processing email {message['id']}: {e}")
            continue

    return len(messages)

def main():
    """Main service loop."""
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment")
        return

    # Initialize Gmail service
    logger.info("Authenticating with Gmail...")
    service = get_gmail_service()

    # Ensure labels exist
    logger.info("Setting up labels...")
    label_ids = ensure_labels_exist(service)

    # Initialize logger
    classification_logger = ClassificationLogger()

    logger.info("Starting inbox classifier service...")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            try:
                count = process_emails(service, label_ids, api_key, classification_logger)
                logger.info(f"Processed {count} emails. Sleeping for 60 seconds...")
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.info("Retrying in 5 minutes...")
                time.sleep(300)
    except KeyboardInterrupt:
        logger.info("Service stopped by user")

if __name__ == '__main__':
    main()
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_main.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add inbox_classifier/main.py tests/test_main.py
git commit -m "Add main service loop"
```

---

## Task 9: Documentation and Setup Instructions

**Files:**
- Modify: `inbox-classifier/README.md`
- Create: `inbox-classifier/docs/usage.md`

**Step 1: Update README with complete setup**

File: `README.md`

```markdown
# Inbox Classifier

AI-powered Gmail inbox classifier using Claude API.

## Features

- Monitors Gmail inbox in real-time
- Classifies emails as Important or Optional using Claude AI
- Applies labels for easy review
- Logs all classification decisions
- Conservative mode - labels only, no auto-archiving

## Setup

### 1. Install Dependencies

```bash
cd inbox-classifier
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up Gmail API

1. Go to https://console.cloud.google.com/
2. Create new project: "Inbox Classifier"
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `credentials.json`
6. Place `credentials.json` in project root

See [docs/setup-gmail.md](docs/setup-gmail.md) for detailed instructions.

### 3. Set up Claude API

1. Get API key from https://console.anthropic.com/
2. Create `.env` file in project root:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### 4. Run the Service

```bash
python -m inbox_classifier.main
```

First run will open browser for Gmail authentication.

## Usage

The service runs continuously and:
- Checks for new unread emails every 60 seconds
- Classifies each email using Claude AI
- Applies labels: `Classifier/Important` or `Classifier/Optional`
- Logs decisions to `~/.inbox-classifier/classifications.jsonl`

View labels in Gmail to review classifications.

## Interacting via Claude Code

Ask Claude Code questions like:
- "Show me what emails were classified today"
- "How many emails were marked as optional this week?"
- "Show me the classification log"

Claude Code can read `~/.inbox-classifier/classifications.jsonl` to answer.

## Running as Background Service (macOS)

See [docs/launchd-setup.md](docs/launchd-setup.md) for setting up automatic startup.

## Cost Estimate

- ~$0.0015 per email classified
- 50 emails/day = ~$2.25/month
- 100 emails/day = ~$4.50/month

## Architecture

See [docs/plans/2026-02-12-inbox-classifier-design.md](docs/plans/2026-02-12-inbox-classifier-design.md)
```

**Step 2: Create usage documentation**

File: `docs/usage.md`

```markdown
# Usage Guide

## Starting the Service

```bash
cd inbox-classifier
source venv/bin/activate
python -m inbox_classifier.main
```

## Reviewing Classifications

### In Gmail

1. Look for labels: `Classifier/Important` and `Classifier/Optional`
2. Review emails marked as Optional
3. If misclassified, manually remove label or move email

### Via Claude Code

Ask questions about your classifications:

**"What emails were classified today?"**
Claude Code will read `~/.inbox-classifier/classifications.jsonl` and show you.

**"Show me emails marked as optional in the last week"**
Claude Code will filter the log by date and classification.

**"How accurate has the classifier been?"**
Claude Code can analyze the log and show statistics.

## Providing Feedback

Currently, feedback is implicit:
- If you move an email from Optional back to inbox → classifier learns from logs
- Future versions will support explicit feedback commands

## Troublesoting

### Service crashes

Check logs in terminal output. Common issues:
- Invalid API key: Check `.env` file
- Gmail auth expired: Delete `~/.inbox-classifier/token.json` and re-authenticate
- Rate limiting: Service will automatically retry

### Classifications incorrect

The system is conservative - when uncertain, it marks as Important.
Review the `reasoning` field in logs to understand decisions.

## Stopping the Service

Press `Ctrl+C` in the terminal.
```

**Step 3: Commit**

```bash
git add README.md docs/usage.md
git commit -m "Add documentation and usage instructions"
```

---

## Task 10: Testing and Validation

**Files:**
- Create: `inbox-classifier/tests/integration_test.md`
- Create: `inbox-classifier/run_tests.sh`

**Step 1: Create test runner script**

File: `run_tests.sh`

```bash
#!/bin/bash
set -e

echo "Running unit tests..."
pytest tests/ -v

echo ""
echo "All tests passed!"
echo ""
echo "To run integration test:"
echo "1. Set up credentials.json and .env"
echo "2. Follow tests/integration_test.md"
```

**Step 2: Make script executable**

```bash
chmod +x run_tests.sh
```

**Step 3: Create integration test guide**

File: `tests/integration_test.md`

```markdown
# Integration Test Guide

Manual integration test to verify end-to-end functionality.

## Prerequisites

- Gmail credentials set up (credentials.json exists)
- API key configured (.env file exists)
- At least 2-3 unread emails in your inbox

## Test Steps

### 1. Run the service

```bash
python -m inbox_classifier.main
```

Expected output:
```
INFO - Authenticating with Gmail...
INFO - Setting up labels...
INFO - Starting inbox classifier service...
INFO - Found N unread emails to classify
INFO - Classified 'Email Subject' as IMPORTANT
...
```

### 2. Check Gmail labels

1. Open Gmail in browser
2. Look for labels: `Classifier/Important` and `Classifier/Optional`
3. Verify emails are labeled correctly

### 3. Check classification log

```bash
cat ~/.inbox-classifier/classifications.jsonl
```

Verify entries contain:
- timestamp
- email_id
- subject
- sender
- classification
- reasoning

### 4. Test Claude Code integration

Ask Claude Code:
```
Read ~/.inbox-classifier/classifications.jsonl and show me what was classified today
```

Verify it can read and parse the log.

### 5. Stop the service

Press `Ctrl+C`

Verify graceful shutdown.

## Success Criteria

- ✓ Service starts without errors
- ✓ Labels are created in Gmail
- ✓ Emails are classified and labeled
- ✓ Log file is created and populated
- ✓ Claude Code can read the log
- ✓ Service stops gracefully
```

**Step 4: Run all unit tests**

```bash
./run_tests.sh
```

Expected: All tests pass

**Step 5: Commit**

```bash
git add tests/integration_test.md run_tests.sh
git commit -m "Add testing and validation scripts"
```

---

## Task 11: Optional - macOS launchd Setup

**Files:**
- Create: `inbox-classifier/docs/launchd-setup.md`
- Create: `inbox-classifier/com.user.inbox-classifier.plist.template`

**Step 1: Create launchd template**

File: `com.user.inbox-classifier.plist.template`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.inbox-classifier</string>
    <key>ProgramArguments</key>
    <array>
        <string>/REPLACE/WITH/VENV/PATH/bin/python</string>
        <string>-m</string>
        <string>inbox_classifier.main</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/REPLACE/WITH/PROJECT/PATH</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ANTHROPIC_API_KEY</key>
        <string>REPLACE_WITH_API_KEY</string>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/inbox-classifier.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/inbox-classifier.err</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

**Step 2: Create setup documentation**

File: `docs/launchd-setup.md`

```markdown
# macOS launchd Setup

Run inbox classifier as background service on macOS.

## Setup

1. Copy and customize the plist file:

```bash
cp com.user.inbox-classifier.plist.template ~/Library/LaunchAgents/com.user.inbox-classifier.plist
```

2. Edit `~/Library/LaunchAgents/com.user.inbox-classifier.plist`:
   - Replace `/REPLACE/WITH/VENV/PATH` with your virtualenv Python path
   - Replace `/REPLACE/WITH/PROJECT/PATH` with project directory
   - Replace `REPLACE_WITH_API_KEY` with your Anthropic API key

3. Load the service:

```bash
launchctl load ~/Library/LaunchAgents/com.user.inbox-classifier.plist
```

## Managing the Service

**Check status:**
```bash
launchctl list | grep inbox-classifier
```

**View logs:**
```bash
tail -f /tmp/inbox-classifier.log
tail -f /tmp/inbox-classifier.err
```

**Stop service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.user.inbox-classifier.plist
```

**Restart service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.user.inbox-classifier.plist
launchctl load ~/Library/LaunchAgents/com.user.inbox-classifier.plist
```

## Troubleshooting

If service doesn't start:
1. Check logs in `/tmp/inbox-classifier.err`
2. Verify paths in plist file are correct
3. Test manually: `python -m inbox_classifier.main`
4. Check permissions on plist file
```

**Step 3: Commit**

```bash
git add docs/launchd-setup.md com.user.inbox-classifier.plist.template
git commit -m "Add macOS launchd setup for background service"
```

---

## Summary

This plan implements a simple, conservative Gmail inbox classifier:

1. **Core functionality**: Polls Gmail every 60 seconds, classifies unread emails with Claude API
2. **Conservative approach**: Only applies labels, no auto-archiving
3. **Logging**: All decisions logged to JSONL for review via Claude Code
4. **Tested**: Unit tests for all components, integration test guide
5. **Production-ready**: Can run as background service via launchd

**Next steps after implementation:**
1. Run integration test to verify functionality
2. Monitor for 1 week to validate classifications
3. If accurate (<5% disagreement), enable auto-archiving in future version
