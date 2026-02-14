# Usage Guide

## Starting the Service

```bash
cd inbox-classifier
source .venv/bin/activate
inbox-classifier
```

Or: `python -m inbox_classifier.main`

## How It Works

1. Every 60 seconds, the service checks for new unread emails in your inbox
2. Emails matching **skip rules** are left untouched (no API call)
3. Remaining emails are classified by Claude AI into your defined categories
4. Classified emails get a Gmail label applied and are archived (removed from inbox)

## Reviewing Classifications

### In Gmail

1. Look for labels matching your categories (e.g., `0_Important`, `1_Routine`, `2_Receipts`)
2. Review emails in each label
3. If misclassified, manually remove label or move email

### Via Claude Code

Ask questions about your classifications:

**"What emails were classified today?"**
Claude Code will read `~/.inbox-classifier/classifications.jsonl` and show you.

**"Show me emails marked as optional in the last week"**
Claude Code will filter the log by date and classification.

**"How accurate has the classifier been?"**
Claude Code can analyze the log and show statistics.

**"reset"**
Resets all classified emails back to inbox as unread for reclassification.

## Configuring Rules

Edit `~/.inbox-classifier/rules.md` to customize categories and skip rules. Changes take effect on the next polling cycle (within 60 seconds) — no restart needed.

### Adding Categories

```markdown
0_Important emails include:
- Security: password resets, security alerts
- Personal: real people asking questions

1_Routine emails include:
- Monthly statements, balance updates
```

### Adding Skip Rules

Keep actionable emails in your inbox by adding skip patterns:

```markdown
Skip classification for:
- from:ebay@ebay.com
- subject:Your item sold
```

Skipped emails stay in your inbox unlabeled — use them as a to-do list and archive manually when done.

## Logs

- **Service log**: `~/.inbox-classifier/service.log` — operational logs (startup, errors, classifications)
- **Classification log**: `~/.inbox-classifier/classifications.jsonl` — structured record of every AI classification decision

## Troubleshooting

### Service crashes

Check `~/.inbox-classifier/service.log`. Common issues:
- Invalid API key: Check `.env` file
- Gmail auth expired: Delete `~/.inbox-classifier/token.json` and re-authenticate
- Rate limiting: Service will automatically retry after 5 minutes

### Classifications incorrect

The system defaults to the first category when uncertain. Review the `reasoning` field in the classification log to understand decisions. Adjust your rules in `rules.md` to improve accuracy.

### Reserved Gmail label names

"Important" is reserved by Gmail. Use a prefix like `0_Important` instead.

## Stopping the Service

Press `Ctrl+C` in the terminal.
