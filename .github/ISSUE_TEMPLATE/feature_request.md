---
name: Feature Request
about: Request a new tool or enhancement
title: '[Feature] '
labels: enhancement
assignees: ''
---

## Summary
<!-- One sentence describing the feature -->

## Use Case
<!-- Why is this needed? What problem does it solve? -->

## Fivetran API Endpoint
<!-- If this maps to a Fivetran API endpoint, provide details -->
- Endpoint: `POST /v1/...` or `GET /v1/...`
- Docs: <!-- Link to Fivetran API docs if available -->

## Proposed Tool Interface
```python
@mcp.tool
async def tool_name(param1: str, param2: bool = False) -> dict[str, Any]:
    """Description of what this tool does.

    Args:
        param1: Description
        param2: Description

    Returns:
        Dictionary with result
    """
```

## Expected Response
```json
{
  "success": true,
  "data": {}
}
```

## Additional Context
<!-- Any other relevant information -->
