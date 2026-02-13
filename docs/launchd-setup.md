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
