# Remote Rules Design

## Problem

The classifier service reads `rules.md` from `~/.inbox-classifier/rules.md` on the local filesystem. When the service moves to a Linux desktop, training from other machines (e.g., MacBook via Claude Code) becomes impossible because the rules file is local to the service host.

Rules belong to the Gmail user, not to the machine running the service.

## Decision

Store `rules.md` in a private GitHub repo (e.g., `longrackslabs/inbox-rules`). The service fetches it via GitHub REST API. Training happens via standard git workflow from any machine with Claude Code.

## Architecture

### Service (read-only consumer)

- New module: `inbox_classifier/rules_loader.py`
- Reads `rules.md` from GitHub REST API using `requests` library
- No git installation required on the service host
- Local cache at `~/.inbox-classifier/rules.md` — used as fallback when GitHub is unreachable
- Cache updated on every successful fetch

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `RULES_REPO` | No | GitHub repo in `owner/repo` format (e.g., `longrackslabs/inbox-rules`) |
| `GITHUB_TOKEN` | When `RULES_REPO` is set | Personal access token with repo read access |

### Backward Compatibility

- If `RULES_REPO` is not set, service reads from local `~/.inbox-classifier/rules.md` (current behavior)
- No breaking changes for existing deployments

### Data Flow

```
Service cycle:
1. Check RULES_REPO env var
2. If set → fetch rules.md via GitHub API (Authorization: Bearer GITHUB_TOKEN)
3. If fetch succeeds → update local cache, use fetched rules
4. If fetch fails → use local cache (log warning)
5. If RULES_REPO not set → read local file (current behavior)
6. Parse categories, classify emails as usual
```

### Trainer SOP (Standard Operating Procedure)

No code changes needed for trainers. Claude Code (or any git client) follows standard git workflow:

1. Clone the rules repo (first time only): `git clone git@github.com:longrackslabs/inbox-rules.git`
2. Pull latest before editing: `git pull`
3. Edit `rules.md` with classification feedback
4. Commit and push: `git add rules.md && git commit -m "..." && git push`
5. Service picks up changes on next poll cycle (within 60 seconds)

Training workflow from the user's perspective stays the same: "check my inbox" → review classifications → give feedback → rules updated. The only difference is Claude Code pushes to GitHub instead of editing a local file.

### Dependencies

- `requests` added to service dependencies (for GitHub API calls)
- GitHub personal access token with `repo` scope (for private repo access)

## Notes

- Skipped emails are marked as read to avoid hitting the Anthropic API repeatedly — this is by design, documented in README
- Future idea: GitHub MCP for Claude Desktop/CoWork could enable training without Claude Code (see `docs/ideas.md`)
