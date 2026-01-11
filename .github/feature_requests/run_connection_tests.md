---
name: New Tool Request
about: Request adding a new MCP tool
title: '[Tool] run_connection_tests - Diagnose connection issues'
labels: new-tool, priority-high
assignees: ''
---

## Tool Name
`run_connection_tests`

## Description
Run setup tests for a Fivetran connection to diagnose connectivity and configuration issues. This is critical for DevOps workflows when a sync fails - it helps identify whether the issue is with credentials, network connectivity, permissions, or configuration.

## Use Case
- **Debugging failed syncs**: When a sync fails, run tests to identify the root cause
- **Validating connection health**: Proactively check if connections are healthy before triggering syncs
- **Post-change validation**: After updating connection config, verify everything still works
- **Incident response**: Quickly diagnose issues during on-call incidents

## Fivetran API Details
- **Method**: POST
- **Endpoint**: `/v1/connections/{connectionId}/test`
- **Docs**: https://fivetran.com/docs/rest-api/api-reference/connections/test-connection

## Input Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `connection_id` | string | Yes | The unique identifier of the connection |

## Expected Output
```json
{
  "success": true,
  "connection_id": "abc123",
  "setup_tests": [
    {
      "title": "Connecting to database",
      "status": "PASSED",
      "message": "Successfully connected"
    },
    {
      "title": "Checking permissions",
      "status": "FAILED",
      "message": "Missing SELECT permission on table X",
      "details": {}
    }
  ]
}
```

## Implementation Notes

### Client Method (`client.py`)
```python
async def run_connection_tests(self, connection_id: str) -> dict[str, Any]:
    """Run setup tests for a connection."""
    return await self._request(
        "POST",
        f"/v1/connections/{connection_id}/test",
    )
```

### Server Tool (`server.py`)
```python
@mcp.tool
async def run_connection_tests(connection_id: str) -> dict[str, Any]:
    """Run setup tests to diagnose connection issues.

    Executes connectivity and configuration tests for a connection.
    Use this to debug sync failures or validate connection health.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary with test results including status and error messages
    """
    client = _get_client()
    result = await client.run_connection_tests(connection_id)
    data = result.get("data", {})

    tests = []
    for test in data.get("setup_tests", []):
        tests.append({
            "title": test.get("title"),
            "status": test.get("status"),
            "message": test.get("message"),
            "details": test.get("details"),
        })

    # Summarize results
    passed = sum(1 for t in tests if t["status"] == "PASSED")
    failed = sum(1 for t in tests if t["status"] in ("FAILED", "JOB_FAILED"))

    return {
        "connection_id": connection_id,
        "passed": passed,
        "failed": failed,
        "all_passed": failed == 0,
        "tests": tests,
    }
```

## Priority
- [x] High - Needed for daily operations
- [ ] Medium - Would improve workflow
- [ ] Low - Nice to have

## Related
- This complements `get_connection_status` which shows current state but doesn't actively test
- Useful to run before `trigger_sync` to ensure connection is healthy
