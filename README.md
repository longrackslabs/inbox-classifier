# Inbox Classifier

AI-powered Gmail inbox classifier using Claude API.

## Features

- Monitors Gmail inbox in real-time
- Classifies emails as Important or Optional using Claude AI
- Applies labels for easy review
- Logs all classification decisions
- Conservative mode - labels only, no auto-archiving

## Setup

### 1. Clone and Install

```bash
gh repo clone longrackslabs/inbox-classifier
cd inbox-classifier
python -m venv .venv
source .venv/bin/activate
pip install -e .
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

## Customizing Classification Rules

Rules live in `~/.inbox-classifier/rules.md` (created on first run with defaults).
Edit this file to change what counts as IMPORTANT vs OPTIONAL — no rebuild needed.

Or ask Claude Code: "make newsletters important" / "add a rule that emails from my boss are always important"

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
