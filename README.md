# Inbox Classifier

AI-powered Gmail inbox classifier using Claude API.

## Features

- Monitors Gmail inbox in real-time
- Classifies emails into dynamic categories using Claude AI
- Applies Gmail labels and archives classified emails
- Skip rules let actionable emails stay in your inbox untouched
- Categories and rules are fully customizable via `rules.md`
- Logs all classification decisions

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
inbox-classifier
```

Or: `python -m inbox_classifier.main`

First run will open browser for Gmail authentication.

## Usage

The service runs continuously and:
- Checks for new unread emails every 60 seconds
- Skips emails matching skip rules (leaves them in inbox, marks as read to avoid reprocessing)
- Classifies remaining emails using Claude AI
- Applies a Gmail label and archives (removes from inbox)
- Logs decisions to `~/.inbox-classifier/classifications.jsonl`
- Service log at `~/.inbox-classifier/service.log`

## Customizing Classification Rules

Rules live in `~/.inbox-classifier/rules.md` (created on first run with defaults). See [rules.md.example](rules.md.example) for a full example. The service re-reads this file every cycle — no restart needed.

### Categories

Define categories with the format `CategoryName emails include:`. Use number prefixes to control Gmail label sort order:

```markdown
0_Important emails include:
- Security: password resets, security alerts, 2FA codes
- Personal: real people asking questions
- Action required: needs response or follow-up

1_Routine emails include:
- Monthly statements, balance updates
- Automated confirmations that don't need action

2_Receipts emails include:
- Purchase receipts and transaction confirmations
- Order confirmations with itemized details

3_Optional emails include:
- Newsletters: regular updates, digests
- Notifications: social media, app updates

4_Ads emails include:
- Promotional: sales, deals, marketing campaigns
- Marketing emails with discount codes
```

Note: "Important" is a reserved Gmail label name. Use a prefix like `0_Important`.

### Skip Rules (Manual Action Queue)

Emails matching skip rules are left in your inbox untouched — no AI call, no label, no archive. Use this for emails that need manual action (eBay sales, bills, etc.).

```markdown
Skip classification for:
- from:ebay@ebay.com
- from:notifications@ebay.com
- subject:Your item sold
- subject:Payment received
```

- `from:` — case-insensitive substring match on sender
- `subject:` — case-insensitive substring match on subject
- Skipped emails stay in your inbox but are marked as read to prevent reprocessing
- No Claude API calls are made for skipped emails (saves cost)

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

## Interacting via Claude Code

Ask Claude Code questions like:
- "Show me what emails were classified today"
- "How many emails were marked as optional this week?"
- "Show me the classification log"
- "reset" — resets all classified emails back to inbox as unread

Claude Code can read `~/.inbox-classifier/classifications.jsonl` to answer.

### Reset

Say "reset" to Claude Code to reprocess all classified emails. This will:

1. Find all messages with classifier labels (0_Important, 1_Routine, etc.)
2. Remove those labels
3. Add INBOX and UNREAD labels back

The service will reclassify them on its next polling cycle. Useful after updating `rules.md` to see how new rules affect existing emails.

## Running as Background Service (macOS)

See [docs/launchd-setup.md](docs/launchd-setup.md) for setting up automatic startup.

## Cost Estimate

- ~$0.0015 per email classified (skipped emails are free)
- 50 emails/day = ~$2.25/month
- 100 emails/day = ~$4.50/month

## Architecture

See [docs/plans/2026-02-12-inbox-classifier-design.md](docs/plans/2026-02-12-inbox-classifier-design.md)
