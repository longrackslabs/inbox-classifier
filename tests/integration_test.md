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
