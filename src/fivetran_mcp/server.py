"""Fivetran MCP Server - expose Fivetran API operations as MCP tools."""

import os
from typing import Any

from fastmcp import FastMCP

from fivetran_mcp.fivetran_api import FivetranClient

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

    Returns comprehensive information including sync state, tasks with full details,
    warnings, and scheduling configuration. Use this for investigating connection
    issues and understanding sync status.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary containing connection details, sync status, tasks, and warnings
        with full details for troubleshooting
    """
    client = _get_client()
    result = await client.get_connection(connection_id)
    data = result.get("data", {})
    status = data.get("status", {})

    # Extract tasks with full details for troubleshooting
    tasks = [
        {
            "code": task.get("code"),
            "message": task.get("message"),
            "details": task.get("details"),
        }
        for task in status.get("tasks", [])
    ]

    # Extract warnings with full details
    warnings = [
        {
            "code": warning.get("code"),
            "message": warning.get("message"),
            "details": warning.get("details"),
        }
        for warning in status.get("warnings", [])
    ]

    return {
        "id": data.get("id"),
        "schema": data.get("schema"),
        "service": data.get("service"),
        "group_id": data.get("group_id"),
        "paused": data.get("paused"),
        "sync_frequency": data.get("sync_frequency"),
        "schedule_type": data.get("schedule_type"),
        "daily_sync_time": data.get("daily_sync_time"),
        "data_delay_sensitivity": data.get("data_delay_sensitivity"),
        "status": {
            "sync_state": status.get("sync_state"),
            "setup_state": status.get("setup_state"),
            "update_state": status.get("update_state"),
            "is_historical_sync": status.get("is_historical_sync"),
            "rescheduled_for": status.get("rescheduled_for"),
            "schema_status": status.get("schema_status"),
        },
        "tasks": tasks,
        "warnings": warnings,
        "source_sync_details": data.get("source_sync_details"),
        "succeeded_at": data.get("succeeded_at"),
        "failed_at": data.get("failed_at"),
        "created_at": data.get("created_at"),
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


@mcp.tool
async def test_connection(connection_id: str) -> dict[str, Any]:
    """Test a Fivetran connection to diagnose connectivity and configuration issues.

    Executes diagnostic tests to identify root causes when syncs fail, validate
    connection health proactively, and support incident response workflows.

    Args:
        connection_id: The unique identifier of the connection to test

    Returns:
        Dictionary containing test results with overall pass/fail status,
        counts of passed/failed tests, and detailed information for each test
    """
    client = _get_client()
    result = await client.test_connection(connection_id)
    data = result.get("data", {})

    tests = [
        {
            "title": test.get("title"),
            "status": test.get("status", "UNKNOWN"),
            "message": test.get("message"),
            "details": test.get("details"),
        }
        for test in data.get("setup_tests", [])
    ]

    passed_count = sum(1 for t in tests if t["status"] == "PASSED")
    failed_count = sum(1 for t in tests if t["status"] == "FAILED")
    all_passed = failed_count == 0 and passed_count > 0

    return {
        "connection_id": connection_id,
        "overall_status": "PASSED" if all_passed else "FAILED",
        "passed_count": passed_count,
        "failed_count": failed_count,
        "total_tests": len(tests),
        "tests": tests,
    }


@mcp.tool
async def get_schema(connection_id: str) -> dict[str, Any]:
    """Retrieve the complete schema configuration for a Fivetran connection.

    Returns all schemas and tables with their enabled/disabled status,
    sync modes, and configuration. Useful for understanding what data
    is being synced and investigating missing tables.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary containing schema configuration with all tables and their status
    """
    client = _get_client()
    result = await client.get_schema(connection_id)
    data = result.get("data", {})

    return {
        "connection_id": connection_id,
        "schema_change_handling": data.get("schema_change_handling"),
        "schemas": data.get("schemas", {}),
    }


@mcp.tool
async def get_connection_schema(
    connection_id: str, table: str | None = None
) -> dict[str, Any]:
    """Retrieve schema information for a Fivetran connection with optional table filter.

    When called without a table parameter, returns all schemas and tables.
    When a table is specified (format: "schema.table_name"), returns detailed
    information for that specific table including all column metadata.

    This is useful for:
    - Debugging dbt model failures when columns are missing
    - Detecting schema changes
    - Building new models with accurate column metadata
    - Identifying which columns are actively synced vs excluded

    Args:
        connection_id: The unique identifier of the connection
        table: Optional table name in "schema.table_name" format to get detailed info

    Returns:
        Dictionary containing schema information. If table is specified, includes
        full column details for that table.
    """
    client = _get_client()

    if table:
        # Parse schema.table format
        parts = table.split(".", 1)
        if len(parts) != 2:
            return {
                "error": f"Invalid table format: '{table}'. Expected 'schema.table_name'",
                "connection_id": connection_id,
            }
        schema_name, table_name = parts

        # Get schema config and column details
        schema_result = await client.get_schema(connection_id)
        columns_result = await client.get_table_columns(
            connection_id, schema_name, table_name
        )

        schemas = schema_result.get("data", {}).get("schemas", {})
        schema_data = schemas.get(schema_name, {})
        table_data = schema_data.get("tables", {}).get(table_name, {})

        columns = [
            {
                "name": col_name,
                "name_in_destination": col_data.get("name_in_destination"),
                "enabled": col_data.get("enabled", False),
                "hashed": col_data.get("hashed", False),
                "is_primary_key": col_data.get("is_primary_key", False),
                "enabled_patch_settings": col_data.get("enabled_patch_settings"),
            }
            for col_name, col_data in columns_result.get("data", {})
            .get("columns", {})
            .items()
        ]

        enabled_columns = sum(1 for c in columns if c["enabled"])
        primary_keys = [c["name"] for c in columns if c["is_primary_key"]]

        return {
            "connection_id": connection_id,
            "schema": schema_name,
            "table": table_name,
            "full_name": table,
            "schema_enabled": schema_data.get("enabled", False),
            "table_enabled": table_data.get("enabled", False),
            "sync_mode": table_data.get("sync_mode"),
            "columns": columns,
            "column_count": len(columns),
            "enabled_column_count": enabled_columns,
            "primary_keys": primary_keys,
        }

    # No table specified - return full schema overview
    result = await client.get_schema(connection_id)
    data = result.get("data", {})
    schemas = data.get("schemas", {})

    # Build summary with table counts
    schema_summary = []
    total_tables = 0
    enabled_tables = 0

    for schema_name, schema_data in schemas.items():
        tables = schema_data.get("tables", {})
        table_count = len(tables)
        enabled_count = sum(
            1 for t in tables.values() if t.get("enabled", False)
        )
        total_tables += table_count
        enabled_tables += enabled_count

        schema_summary.append({
            "schema": schema_name,
            "enabled": schema_data.get("enabled", False),
            "table_count": table_count,
            "enabled_table_count": enabled_count,
        })

    return {
        "connection_id": connection_id,
        "schema_change_handling": data.get("schema_change_handling"),
        "total_schemas": len(schemas),
        "total_tables": total_tables,
        "enabled_tables": enabled_tables,
        "schemas": schema_summary,
    }


@mcp.tool
async def list_tables(connection_id: str) -> dict[str, Any]:
    """List all tables in a Fivetran connection with their sync status.

    Provides a flattened view of all tables across all schemas,
    showing enabled status, sync mode, and configuration.
    Useful for quickly seeing which tables are being synced.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary containing a flat list of all tables with their status
    """
    client = _get_client()
    result = await client.get_schema(connection_id)
    schemas = result.get("data", {}).get("schemas", {})

    tables = []
    for schema_name, schema_data in schemas.items():
        schema_enabled = schema_data.get("enabled", False)
        for table_name, table_data in schema_data.get("tables", {}).items():
            tables.append({
                "schema": schema_name,
                "table": table_name,
                "full_name": f"{schema_name}.{table_name}",
                "enabled": table_data.get("enabled", False),
                "schema_enabled": schema_enabled,
                "sync_mode": table_data.get("sync_mode"),
                "enabled_patch_settings": table_data.get("enabled_patch_settings", {}),
            })

    return {
        "connection_id": connection_id,
        "tables": tables,
        "count": len(tables),
        "enabled_count": sum(1 for t in tables if t["enabled"]),
    }


@mcp.tool
async def get_table_columns(
    connection_id: str, schema: str, table: str
) -> dict[str, Any]:
    """Retrieve column details for a specific table in a Fivetran connection.

    Returns column names, sync configuration, and metadata. Useful for
    investigating schema issues or understanding table structure.

    Note: Column data types are not available via the Fivetran API.
    Data types can be queried directly from your destination database.

    Args:
        connection_id: The unique identifier of the connection
        schema: The schema name containing the table
        table: The table name to get columns for

    Returns:
        Dictionary containing column details including names, enabled status,
        primary key info, and sync settings
    """
    client = _get_client()
    result = await client.get_table_columns(connection_id, schema, table)
    data = result.get("data", {})

    columns = [
        {
            "name": col_name,
            "name_in_destination": col_data.get("name_in_destination"),
            "enabled": col_data.get("enabled", False),
            "hashed": col_data.get("hashed", False),
            "is_primary_key": col_data.get("is_primary_key", False),
            "enabled_patch_settings": col_data.get("enabled_patch_settings"),
        }
        for col_name, col_data in data.get("columns", {}).items()
    ]

    enabled_count = sum(1 for c in columns if c["enabled"])
    primary_keys = [c["name"] for c in columns if c["is_primary_key"]]

    return {
        "connection_id": connection_id,
        "schema": schema,
        "table": table,
        "columns": columns,
        "column_count": len(columns),
        "enabled_count": enabled_count,
        "primary_keys": primary_keys,
    }


@mcp.tool
async def reload_schema(connection_id: str) -> dict[str, Any]:
    """Reload the schema configuration from the source for a Fivetran connection.

    Fetches the latest schema from the data source and updates the configuration.
    Useful after source schema changes to detect new tables or columns.

    Args:
        connection_id: The unique identifier of the connection

    Returns:
        Dictionary confirming the schema reload was triggered
    """
    client = _get_client()
    await client.reload_schema(connection_id)

    return {
        "success": True,
        "connection_id": connection_id,
        "message": "Schema reload triggered successfully",
    }


@mcp.tool
async def get_table_status(
    connection_id: str,
    schema_filter: str | None = None,
    enabled_only: bool = False,
) -> dict[str, Any]:
    """Get per-table sync status for a Fivetran connection.

    Returns detailed status for each table including enabled/disabled state,
    sync configuration, and metadata from the most recent successful sync.
    Useful for debugging large connectors with many tables, identifying
    stale tables, and monitoring data freshness.

    For connectors with many tables (e.g., Airtable with 20+ bases, or Postgres
    with 50+ tables), this provides visibility into which specific tables are
    configured and their sync settings.

    Note: Table metadata (like destination names) is only available after
    at least one successful sync has completed.

    Args:
        connection_id: The unique identifier of the connection
        schema_filter: Optional schema name to filter tables (e.g., "public")
        enabled_only: If True, only return tables that are enabled for sync

    Returns:
        Dictionary containing per-table status including:
        - Table name and schema
        - Enabled/disabled state
        - Sync mode configuration
        - Destination name (if available from metadata)
    """
    client = _get_client()

    # Fetch schema config and table metadata in parallel
    schema_result = await client.get_schema(connection_id)
    schemas_data = schema_result.get("data", {}).get("schemas", {})

    # Try to get table metadata (may fail if no successful sync yet)
    metadata_map: dict[str, dict[str, Any]] = {}
    try:
        metadata_result = await client.get_table_metadata(connection_id)
        for table in metadata_result.get("data", {}).get("items", []):
            # Key by schema.table for lookup
            key = f"{table.get('schema')}.{table.get('table')}"
            metadata_map[key] = table
    except Exception:
        # Metadata not available yet (no successful sync)
        pass

    # Build table status list
    tables = []
    for schema_name, schema_data in schemas_data.items():
        # Apply schema filter if specified
        if schema_filter and schema_name != schema_filter:
            continue

        schema_enabled = schema_data.get("enabled", False)

        for table_name, table_data in schema_data.get("tables", {}).items():
            table_enabled = table_data.get("enabled", False)

            # Apply enabled filter if specified
            if enabled_only and not table_enabled:
                continue

            full_name = f"{schema_name}.{table_name}"
            metadata = metadata_map.get(full_name, {})

            # Determine effective sync state
            if not schema_enabled:
                sync_state = "schema_disabled"
            elif not table_enabled:
                sync_state = "disabled"
            else:
                sync_state = "enabled"

            table_status = {
                "schema": schema_name,
                "table": table_name,
                "full_name": full_name,
                "sync_state": sync_state,
                "enabled": table_enabled,
                "schema_enabled": schema_enabled,
                "sync_mode": table_data.get("sync_mode"),
                "enabled_patch_settings": table_data.get("enabled_patch_settings", {}),
            }

            # Add metadata if available
            if metadata:
                table_status["name_in_destination"] = metadata.get("name_in_destination")
                table_status["schema_in_destination"] = metadata.get("parent_id")

            tables.append(table_status)

    # Calculate summary statistics
    enabled_count = sum(1 for t in tables if t["sync_state"] == "enabled")
    disabled_count = sum(1 for t in tables if t["sync_state"] == "disabled")
    schema_disabled_count = sum(1 for t in tables if t["sync_state"] == "schema_disabled")

    return {
        "connection_id": connection_id,
        "tables": tables,
        "summary": {
            "total_tables": len(tables),
            "enabled": enabled_count,
            "disabled": disabled_count,
            "schema_disabled": schema_disabled_count,
        },
        "metadata_available": len(metadata_map) > 0,
        "filters_applied": {
            "schema_filter": schema_filter,
            "enabled_only": enabled_only,
        },
    }


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
