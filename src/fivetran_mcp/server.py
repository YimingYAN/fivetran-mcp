"""Fivetran MCP Server - expose Fivetran API operations as MCP tools."""

import os
from typing import Any

from fastmcp import FastMCP

from fivetran_mcp.client import FivetranClient

mcp = FastMCP(name="Fivetran MCP Server")

_client: FivetranClient | None = None


@mcp.tool
async def list_connections(
    limit: int = 100, group_id: str | None = None
) -> dict[str, Any]:
    """List all Fivetran connections in the account.

    Args:
        limit: Maximum number of connections to return (1-1000, default 100)
        group_id: Optional group ID to filter connections by group

    Returns:
        Dictionary containing list of connections with their IDs, names, status, and sync state
    """
    client = _get_client()
    if group_id:
        result = await client.list_connections_in_group(group_id, limit=limit)
    else:
        result = await client.list_connections(limit=limit)

    connections = [
        _extract_connection_summary(conn)
        for conn in result.get("data", {}).get("items", [])
    ]
    return {"connections": connections, "count": len(connections)}


@mcp.tool
async def get_connection_status(connection_id: str) -> dict[str, Any]:
    """Get detailed status for a specific Fivetran connection.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary containing connection details, sync status, and any warnings/tasks
    """
    client = _get_client()
    result = await client.get_connection(connection_id)
    data = result.get("data", {})
    status = data.get("status", {})

    return {
        "id": data.get("id"),
        "schema": data.get("schema"),
        "service": data.get("service"),
        "group_id": data.get("group_id"),
        "paused": data.get("paused"),
        "sync_frequency": data.get("sync_frequency"),
        "schedule_type": data.get("schedule_type"),
        "status": {
            "sync_state": status.get("sync_state"),
            "setup_state": status.get("setup_state"),
            "update_state": status.get("update_state"),
            "is_historical_sync": status.get("is_historical_sync"),
            "rescheduled_for": status.get("rescheduled_for"),
        },
        "tasks": status.get("tasks", []),
        "warnings": status.get("warnings", []),
        "succeeded_at": data.get("succeeded_at"),
        "failed_at": data.get("failed_at"),
    }


@mcp.tool
async def trigger_sync(connection_id: str, force: bool = False) -> dict[str, Any]:
    """Trigger a data sync for a Fivetran connection.

    This starts a sync without waiting for the next scheduled sync time.
    Does not override the standard sync frequency.

    Args:
        connection_id: The unique identifier of the connection
        force: If True, force the sync even if one is already in progress

    Returns:
        Dictionary with sync trigger confirmation
    """
    client = _get_client()
    result = await client.trigger_sync(connection_id, force=force)
    return {
        "success": True,
        "message": result.get("message", "Sync triggered successfully"),
        "connection_id": connection_id,
    }


@mcp.tool
async def trigger_resync(connection_id: str) -> dict[str, Any]:
    """Trigger a full historical resync for a Fivetran connection.

    This re-syncs all historical data from the source. Use with caution
    as it may take significant time and resources.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary with resync trigger confirmation
    """
    client = _get_client()
    result = await client.trigger_resync(connection_id)
    return {
        "success": True,
        "message": result.get("message", "Historical resync triggered successfully"),
        "connection_id": connection_id,
    }


@mcp.tool
async def resync_tables(connection_id: str, tables: list[str]) -> dict[str, Any]:
    """Trigger a historical resync for specific tables within a connection.

    This re-syncs historical data only for the specified tables, not the entire
    connection. Useful when you need to refresh specific tables without a full resync.

    Args:
        connection_id: The unique identifier of the connection
        tables: List of table names to resync (e.g., ["schema.table_name", "public.users"])

    Returns:
        Dictionary with resync trigger confirmation
    """
    client = _get_client()
    result = await client.resync_tables(connection_id, tables)
    return {
        "success": True,
        "message": result.get("message", "Table resync triggered successfully"),
        "connection_id": connection_id,
        "tables": tables,
    }


@mcp.tool
async def pause_connection(connection_id: str) -> dict[str, Any]:
    """Pause a Fivetran connection.

    Paused connections will not sync data until resumed.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary with updated connection status
    """
    client = _get_client()
    result = await client.pause_connection(connection_id)
    data = result.get("data", {})
    return {
        "success": True,
        "connection_id": connection_id,
        "paused": data.get("paused", True),
        "message": "Connection paused successfully",
    }


@mcp.tool
async def resume_connection(connection_id: str) -> dict[str, Any]:
    """Resume a paused Fivetran connection.

    The connection will start syncing according to its schedule.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary with updated connection status
    """
    client = _get_client()
    result = await client.resume_connection(connection_id)
    data = result.get("data", {})
    return {
        "success": True,
        "connection_id": connection_id,
        "paused": data.get("paused", False),
        "message": "Connection resumed successfully",
    }


@mcp.tool
async def list_groups(limit: int = 100) -> dict[str, Any]:
    """List all Fivetran groups (destinations) in the account.

    Groups represent destinations where data is synced to.

    Args:
        limit: Maximum number of groups to return (1-1000, default 100)

    Returns:
        Dictionary containing list of groups with their IDs and names
    """
    client = _get_client()
    result = await client.list_groups(limit=limit)

    groups = [
        {"id": group.get("id"), "name": group.get("name"), "created_at": group.get("created_at")}
        for group in result.get("data", {}).get("items", [])
    ]
    return {"groups": groups, "count": len(groups)}


def main() -> None:
    """Run the MCP server."""
    mcp.run()


def _get_client() -> FivetranClient:
    """Get or create the Fivetran API client."""
    global _client
    if _client is not None:
        return _client

    api_key = os.environ.get("FIVETRAN_SYNC_API_KEY") or os.environ.get("FIVETRAN_API_KEY")
    api_secret = os.environ.get("FIVETRAN_SYNC_API_SECRET") or os.environ.get("FIVETRAN_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError(
            "FIVETRAN_SYNC_API_KEY and FIVETRAN_SYNC_API_SECRET "
            "(or FIVETRAN_API_KEY and FIVETRAN_API_SECRET) environment variables are required"
        )

    _client = FivetranClient(api_key, api_secret)
    return _client


def _extract_connection_summary(conn: dict[str, Any]) -> dict[str, Any]:
    """Extract a summary of connection data for list responses."""
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


if __name__ == "__main__":
    main()
