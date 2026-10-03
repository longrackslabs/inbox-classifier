# Intelligent Inbox Classifier - Design Document

**Date:** 2026-02-12
**Status:** Approved
**Target:** Personal Gmail account

## Problem Statement

Email inbox gets cluttered with newsletters, promotions, and notifications that aren't urgent. Need an intelligent system to identify which emails are important vs. which can be safely archived, without false positives on important messages.

## Design Goals

1. **Conservative first** - Label suggestions only, no auto-archiving until proven reliable
2. **Simple implementation** - Start with core functionality, add complexity only if needed
3. **AI-powered** - Use Claude API for intelligent classification
4. **Claude Code integration** - Review and interact via natural language commands

## Architecture

### Core Components

**1. Background Service (Python)**
- Monitors Gmail inbox for new unread emails using Gmail API
- Runs continuously as a macOS launchd service
- Polls every 60 seconds for new emails (simple polling, not push notifications initially)

**2. AI Classifier**
- For each new unread email, send to Claude API:
  - Subject line
  - Sender (name and email)
  - First 300 characters of body
  - Prompt: "Is this email important (needs to stay in inbox) or optional (can be archived)? Consider: transactional emails, receipts, security alerts, personal messages, and work emails are important. Newsletters, promotions, notifications, and bulk emails are optional."
- Claude returns: `IMPORTANT` or `OPTIONAL` with brief reasoning

**3. Action Executor**
- Apply Gmail label based on classification:
  - `Classifier/Important` - Keep in inbox
  - `Classifier/Optional` - Suggest archiving
- **Phase 1:** Do not archive anything, only apply labels
- **Future:** Add auto-archiving once system proves reliable

**4. State & Logging**
- Log all classifications to local JSON file: `~/.inbox-classifier/classifications.jsonl`
- Each entry: `{timestamp, email_id, subject, sender, classification, reasoning}`
- Claude Code reads this log to answer questions like "what did you classify today?"

### Data Flow

```
1. Poll Gmail API for unread emails in INBOX
2. For each new email:
   a. Check if already classified (has Classifier/* label) → skip
   b. Send to Claude API for classification
   c. Apply appropriate Gmail label
   d. Log decision to classifications.jsonl
3. Sleep 60 seconds, repeat
```

## Implementation Details

### Gmail API Integration

- Use OAuth 2.0 for authentication (store tokens in `~/.inbox-classifier/token.json`)
- Required scopes: `gmail.readonly`, `gmail.modify` (for labels)
- Create custom labels if they don't exist: `Classifier/Important`, `Classifier/Optional`

### Claude API Integration

- Use Anthropic Python SDK
- Model: `claude-sonnet-4-5` (balance of cost and quality)
- Store API key in environment variable or macOS keychain
- Rate limiting: Max 1 request per second to avoid API throttling

### Error Handling

- If Gmail API fails: Log error, retry after 5 minutes
- If Claude API fails: Log error, skip email (try again on next poll)
- If rate limited: Back off exponentially

### Cost Estimation

- Average email classification: ~200 input tokens + 50 output tokens
- Cost per email: ~$0.0015
- For 100 emails/day: ~$4.50/month
- For 50 emails/day: ~$2.25/month

## Future Enhancements (Not in V1)

1. **Auto-archiving** - Once confident, automatically archive `Optional` emails
2. **Whitelist** - Never archive emails from specific senders
3. **Learning** - Track when user moves emails back to inbox (false positive)
4. **Heuristics** - Add fast pre-filters for obvious cases to reduce API costs
5. **Push notifications** - Use Gmail push instead of polling for real-time processing
6. **Batch processing** - Process multiple emails in single API call to reduce costs

## Success Criteria

**Phase 1 (Launch):**
- Service runs reliably for 1 week without crashes
- Labels are applied correctly (can verify in Gmail)
- Can query classification history via Claude Code
- No important emails misclassified as optional (zero false positives acceptable)

**Phase 2 (Auto-archive):**
- After reviewing 100+ classifications with <5% disagreement
- Enable auto-archiving for `Optional` emails
- Monitor for false positives weekly

## Open Questions

- None at this time

## Non-Goals

- Multi-account support
- Complex rule-based filtering
- Machine learning model training
- Real-time push notifications (use polling initially)
- Web dashboard UI
