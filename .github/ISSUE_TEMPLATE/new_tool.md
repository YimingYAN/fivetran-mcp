---
name: New Tool Request
about: Request adding a new MCP tool
title: '[Tool] '
labels: ''
assignees: ''
---

## Tool Name
<!-- e.g., run_connection_tests, get_sync_history -->

## Description
<!-- What should this tool do? Why is it needed? -->

## Use Case
<!-- Specific scenarios where this tool would be used -->
-
-

## Fivetran API Details
- **Method**: GET / POST / PATCH / DELETE
- **Endpoint**: `/v1/...`
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

## Implementation

### Client Method (`client.py`)
```python
async def method_name(self, connection_id: str) -> dict[str, Any]:
    """Description."""
    return await self._request(
        "POST",  # or GET, PATCH, DELETE
        f"/v1/connections/{connection_id}/...",
    )
```

### Server Tool (`server.py`)
```python
@mcp.tool
async def tool_name(connection_id: str) -> dict[str, Any]:
    """Description of what this tool does.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary with result
    """
    client = _get_client()
    result = await client.method_name(connection_id)
    data = result.get("data", {})

    return {
        "success": True,
        "connection_id": connection_id,
        "data": data,
    }
```

## Acceptance Criteria
- [ ] Client method added to `client.py`
- [ ] Tool added to `server.py` with `@mcp.tool` decorator
- [ ] Docstring with Args and Returns
- [ ] README updated with new tool in table
- [ ] Tested with Fivetran API

## Priority
- [ ] High - Needed for daily operations
- [ ] Medium - Would improve workflow
- [ ] Low - Nice to have
