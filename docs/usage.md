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

## Troubleshooting

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
