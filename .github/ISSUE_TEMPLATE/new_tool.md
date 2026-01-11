---
name: New Tool Request
about: Request adding a new MCP tool
title: '[Tool] '
labels: new-tool
assignees: ''
---

## Tool Name
<!-- e.g., get_sync_history, update_schedule -->

## Description
<!-- What should this tool do? -->

## Fivetran API Details
- **Method**: GET / POST / PATCH / DELETE
- **Endpoint**: `/v1/connections/...`
- **Docs**: <!-- Link to Fivetran API documentation -->

## Input Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `connection_id` | string | Yes | The connection identifier |
| | | | |

## Expected Output
```json
{
  "success": true,
  "connection_id": "abc123",
  "data": {}
}
```

## Implementation Notes
<!-- Any specific details about how this should be implemented -->

## Priority
- [ ] High - Needed for daily operations
- [ ] Medium - Would improve workflow
- [ ] Low - Nice to have
