"""Cloudflare Workers entry point for Fivetran MCP Server.

This module adapts the FastMCP-based Fivetran MCP server to run on
Cloudflare Workers using Streamable HTTP transport.

Note: Cloudflare Python Workers are in beta. Some features may change.
"""

import json
from typing import Any

from js import Response, Headers, fetch
from pyodide.ffi import to_js

# Base64 encoding for Fivetran API auth
import base64


class FivetranClient:
    """Async HTTP client for Fivetran API (Cloudflare Workers version)."""

    BASE_URL = "https://api.fivetran.com/v1"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        credentials = f"{api_key}:{api_secret}"
        self._auth_header = f"Basic {base64.b64encode(credentials.encode()).decode()}"

    async def _request(self, method: str, path: str, data: dict | None = None) -> dict:
        """Make an authenticated request to Fivetran API."""
        url = f"{self.BASE_URL}{path}"
        headers = to_js({
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        options = {"method": method, "headers": headers}
        if data:
            options["body"] = json.dumps(data)

        response = await fetch(url, to_js(options, dict_converter=lambda d: d))
        text = await response.text()
        return json.loads(text) if text else {}

    async def list_connections(self, limit: int = 100) -> dict:
        return await self._request("GET", f"/connections?limit={limit}")

    async def list_connections_in_group(self, group_id: str, limit: int = 100) -> dict:
        return await self._request("GET", f"/groups/{group_id}/connectors?limit={limit}")

    async def get_connection(self, connection_id: str) -> dict:
        return await self._request("GET", f"/connectors/{connection_id}")

    async def trigger_sync(self, connection_id: str, force: bool = False) -> dict:
        return await self._request("POST", f"/connectors/{connection_id}/sync", {"force": force})

    async def trigger_resync(self, connection_id: str) -> dict:
        return await self._request("POST", f"/connectors/{connection_id}/resync")

    async def resync_tables(self, connection_id: str, tables: list[str]) -> dict:
        # Parse tables into schema/table format
        table_objects = {}
        for table in tables:
            parts = table.split(".", 1)
            if len(parts) == 2:
                schema, table_name = parts
                if schema not in table_objects:
                    table_objects[schema] = {"tables": {}}
                table_objects[schema]["tables"][table_name] = {}
        return await self._request("POST", f"/connectors/{connection_id}/schemas/tables/resync", {"schemas": table_objects})

    async def pause_connection(self, connection_id: str) -> dict:
        return await self._request("PATCH", f"/connectors/{connection_id}", {"paused": True})

    async def resume_connection(self, connection_id: str) -> dict:
        return await self._request("PATCH", f"/connectors/{connection_id}", {"paused": False})

    async def list_groups(self, limit: int = 100) -> dict:
        return await self._request("GET", f"/groups?limit={limit}")

    async def test_connection(self, connection_id: str) -> dict:
        return await self._request("POST", f"/connectors/{connection_id}/test")

    async def get_schema(self, connection_id: str) -> dict:
        return await self._request("GET", f"/connectors/{connection_id}/schemas")

    async def get_table_columns(self, connection_id: str, schema: str, table: str) -> dict:
        return await self._request("GET", f"/connectors/{connection_id}/schemas/{schema}/tables/{table}/columns")

    async def reload_schema(self, connection_id: str) -> dict:
        return await self._request("POST", f"/connectors/{connection_id}/schemas/reload")


# Tool definitions for MCP
TOOLS = {
    "list_connections": {
        "description": "List all Fivetran connections in the account",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 100, "description": "Maximum number of connections to return"},
                "group_id": {"type": "string", "description": "Optional group ID to filter connections"},
            },
        },
    },
    "get_connection_status": {
        "description": "Get detailed status for a specific Fivetran connection",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
            },
            "required": ["connection_id"],
        },
    },
    "trigger_sync": {
        "description": "Trigger a data sync for a Fivetran connection",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
                "force": {"type": "boolean", "default": False, "description": "Force sync even if one is in progress"},
            },
            "required": ["connection_id"],
        },
    },
    "trigger_resync": {
        "description": "Trigger a full historical resync for a connection",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
            },
            "required": ["connection_id"],
        },
    },
    "resync_tables": {
        "description": "Resync specific tables within a connection",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
                "tables": {"type": "array", "items": {"type": "string"}, "description": "List of table names (schema.table)"},
            },
            "required": ["connection_id", "tables"],
        },
    },
    "pause_connection": {
        "description": "Pause a Fivetran connection",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
            },
            "required": ["connection_id"],
        },
    },
    "resume_connection": {
        "description": "Resume a paused Fivetran connection",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
            },
            "required": ["connection_id"],
        },
    },
    "list_groups": {
        "description": "List all Fivetran groups (destinations)",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 100, "description": "Maximum number of groups to return"},
            },
        },
    },
    "test_connection": {
        "description": "Test a Fivetran connection to diagnose issues",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
            },
            "required": ["connection_id"],
        },
    },
    "get_schema": {
        "description": "Get complete schema configuration for a connection",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
            },
            "required": ["connection_id"],
        },
    },
    "list_tables": {
        "description": "List all tables in a connection with sync status",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
            },
            "required": ["connection_id"],
        },
    },
    "reload_schema": {
        "description": "Reload schema configuration from the source",
        "parameters": {
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "description": "The unique identifier of the connection"},
            },
            "required": ["connection_id"],
        },
    },
}


def _extract_connection_summary(conn: dict) -> dict:
    """Extract a summary of connection data."""
    status = conn.get("status", {})
    return {
        "id": conn.get("id"),
        "schema": conn.get("schema"),
        "service": conn.get("service"),
        "group_id": conn.get("group_id"),
        "paused": conn.get("paused"),
        "sync_state": status.get("sync_state"),
        "setup_state": status.get("setup_state"),
        "is_historical_sync": status.get("is_historical_sync"),
        "succeeded_at": conn.get("succeeded_at"),
        "failed_at": conn.get("failed_at"),
    }


async def execute_tool(client: FivetranClient, tool_name: str, args: dict) -> dict:
    """Execute an MCP tool and return the result."""
    if tool_name == "list_connections":
        limit = args.get("limit", 100)
        group_id = args.get("group_id")
        if group_id:
            result = await client.list_connections_in_group(group_id, limit=limit)
        else:
            result = await client.list_connections(limit=limit)
        connections = [_extract_connection_summary(conn) for conn in result.get("data", {}).get("items", [])]
        return {"connections": connections, "count": len(connections)}

    elif tool_name == "get_connection_status":
        result = await client.get_connection(args["connection_id"])
        data = result.get("data", {})
        status = data.get("status", {})
        tasks = [{"code": t.get("code"), "message": t.get("message"), "details": t.get("details")} for t in status.get("tasks", [])]
        warnings = [{"code": w.get("code"), "message": w.get("message"), "details": w.get("details")} for w in status.get("warnings", [])]
        return {
            "id": data.get("id"),
            "schema": data.get("schema"),
            "service": data.get("service"),
            "group_id": data.get("group_id"),
            "paused": data.get("paused"),
            "status": {
                "sync_state": status.get("sync_state"),
                "setup_state": status.get("setup_state"),
                "update_state": status.get("update_state"),
                "is_historical_sync": status.get("is_historical_sync"),
            },
            "tasks": tasks,
            "warnings": warnings,
            "succeeded_at": data.get("succeeded_at"),
            "failed_at": data.get("failed_at"),
        }

    elif tool_name == "trigger_sync":
        await client.trigger_sync(args["connection_id"], force=args.get("force", False))
        return {"success": True, "message": "Sync triggered successfully", "connection_id": args["connection_id"]}

    elif tool_name == "trigger_resync":
        await client.trigger_resync(args["connection_id"])
        return {"success": True, "message": "Historical resync triggered successfully", "connection_id": args["connection_id"]}

    elif tool_name == "resync_tables":
        await client.resync_tables(args["connection_id"], args["tables"])
        return {"success": True, "message": "Table resync triggered successfully", "connection_id": args["connection_id"], "tables": args["tables"]}

    elif tool_name == "pause_connection":
        await client.pause_connection(args["connection_id"])
        return {"success": True, "connection_id": args["connection_id"], "paused": True, "message": "Connection paused successfully"}

    elif tool_name == "resume_connection":
        await client.resume_connection(args["connection_id"])
        return {"success": True, "connection_id": args["connection_id"], "paused": False, "message": "Connection resumed successfully"}

    elif tool_name == "list_groups":
        result = await client.list_groups(limit=args.get("limit", 100))
        groups = [{"id": g.get("id"), "name": g.get("name"), "created_at": g.get("created_at")} for g in result.get("data", {}).get("items", [])]
        return {"groups": groups, "count": len(groups)}

    elif tool_name == "test_connection":
        result = await client.test_connection(args["connection_id"])
        data = result.get("data", {})
        tests = [{"title": t.get("title"), "status": t.get("status", "UNKNOWN"), "message": t.get("message")} for t in data.get("setup_tests", [])]
        passed = sum(1 for t in tests if t["status"] == "PASSED")
        failed = sum(1 for t in tests if t["status"] == "FAILED")
        return {
            "connection_id": args["connection_id"],
            "overall_status": "PASSED" if failed == 0 and passed > 0 else "FAILED",
            "passed_count": passed,
            "failed_count": failed,
            "tests": tests,
        }

    elif tool_name == "get_schema":
        result = await client.get_schema(args["connection_id"])
        data = result.get("data", {})
        return {"connection_id": args["connection_id"], "schema_change_handling": data.get("schema_change_handling"), "schemas": data.get("schemas", {})}

    elif tool_name == "list_tables":
        result = await client.get_schema(args["connection_id"])
        schemas = result.get("data", {}).get("schemas", {})
        tables = []
        for schema_name, schema_data in schemas.items():
            for table_name, table_data in schema_data.get("tables", {}).items():
                tables.append({
                    "schema": schema_name,
                    "table": table_name,
                    "full_name": f"{schema_name}.{table_name}",
                    "enabled": table_data.get("enabled", False),
                    "sync_mode": table_data.get("sync_mode"),
                })
        return {"connection_id": args["connection_id"], "tables": tables, "count": len(tables)}

    elif tool_name == "reload_schema":
        await client.reload_schema(args["connection_id"])
        return {"success": True, "connection_id": args["connection_id"], "message": "Schema reload triggered successfully"}

    else:
        return {"error": f"Unknown tool: {tool_name}"}


def json_response(data: Any, status: int = 200) -> Response:
    """Create a JSON response."""
    headers = Headers.new(to_js({"Content-Type": "application/json"}))
    return Response.new(json.dumps(data), to_js({"status": status, "headers": headers}))


async def on_fetch(request, env) -> Response:
    """Handle incoming HTTP requests (Cloudflare Workers entry point)."""
    url = request.url
    method = request.method
    path = url.split("?")[0].rstrip("/").split("/")[-1] if "/" in url else ""

    # CORS preflight
    if method == "OPTIONS":
        headers = Headers.new(to_js({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }))
        return Response.new("", to_js({"status": 204, "headers": headers}))

    # Health check
    if path == "" or path == "health":
        return json_response({"status": "ok", "server": "Fivetran MCP Server"})

    # MCP endpoint info
    if path == "mcp":
        return json_response({
            "name": "Fivetran MCP Server",
            "version": "0.3.0",
            "protocol": "mcp",
            "transport": "streamable-http",
        })

    # List available tools
    if path == "tools":
        return json_response({"tools": TOOLS})

    # Execute tool
    if path == "execute" and method == "POST":
        try:
            body = await request.text()
            data = json.loads(body)
            tool_name = data.get("tool")
            args = data.get("arguments", {})

            if not tool_name:
                return json_response({"error": "Missing 'tool' field"}, 400)
            if tool_name not in TOOLS:
                return json_response({"error": f"Unknown tool: {tool_name}"}, 400)

            # Get API credentials from environment
            api_key = getattr(env, "FIVETRAN_API_KEY", None)
            api_secret = getattr(env, "FIVETRAN_API_SECRET", None)

            if not api_key or not api_secret:
                return json_response({"error": "FIVETRAN_API_KEY and FIVETRAN_API_SECRET must be configured"}, 500)

            client = FivetranClient(api_key, api_secret)
            result = await execute_tool(client, tool_name, args)
            return json_response({"result": result})

        except json.JSONDecodeError:
            return json_response({"error": "Invalid JSON"}, 400)
        except Exception as e:
            return json_response({"error": str(e)}, 500)

    return json_response({"error": "Not found"}, 404)
