---
name: Bug Report
about: Report a bug or unexpected behavior
title: '[Bug] '
labels: ''
assignees: ''
---

## Summary
<!-- One sentence describing the bug -->

## MCP Tool
<!-- Which tool was being used? -->
- Tool: `list_connections` / `trigger_sync` / `get_connection_status` / etc.

## Current Behavior
<!-- What happens now -->

## Expected Behavior
<!-- What should happen -->

## Steps to Reproduce
```bash
# Commands or code to reproduce the issue
```

## Error Output
```
# Paste full error message/stack trace here
```

## Fivetran API Response
<!-- If applicable, what did the Fivetran API return? -->
```json
{
  "code": "...",
  "message": "..."
}
```

## Environment
- Python version:
- OS:
- fivetran-mcp version:

## Relevant Code
<!-- Reference specific files/functions -->
- File: `src/fivetran_mcp/client.py` or `server.py`
- Function/Method:

## Suggested Fix
<!-- Optional: If you have ideas on how to fix this -->

## Acceptance Criteria
- [ ] Bug can no longer be reproduced
- [ ] Error handling added (if applicable)
- [ ] Tests pass
