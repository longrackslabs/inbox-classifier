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
