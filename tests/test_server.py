"""Tests for Fivetran MCP server tools."""

import os
from unittest.mock import patch

import httpx
import pytest
import respx

from fivetran_mcp import server


# Access the underlying functions (not the FunctionTool wrappers)
# Using underscore prefix to avoid pytest picking them up as test functions
_get_connection_status = server.get_connection_status.fn
_get_schema = server.get_schema.fn
_get_connection_schema = server.get_connection_schema.fn
_list_tables = server.list_tables.fn
_get_table_columns = server.get_table_columns.fn
_reload_schema = server.reload_schema.fn
_test_connection = server.test_connection.fn


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the global client before each test."""
    server._client = None
    yield
    server._client = None


@pytest.fixture
def mock_env():
    """Fixture that sets required environment variables."""
    with patch.dict(os.environ, {
        "FIVETRAN_API_KEY": "test_key",
        "FIVETRAN_API_SECRET": "test_secret",
    }):
        yield


@pytest.mark.asyncio
async def test_get_connection_status_with_details(mock_env, mock_api):
    """Test get_connection_status returns full task and warning details."""
    mock_api.get("/v1/connections/conn_123").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "id": "conn_123",
                    "schema": "test_schema",
                    "service": "postgres",
                    "group_id": "group_1",
                    "paused": False,
                    "sync_frequency": 360,
                    "schedule_type": "auto",
                    "daily_sync_time": "03:00",
                    "data_delay_sensitivity": "NORMAL",
                    "succeeded_at": "2024-01-01T00:00:00Z",
                    "failed_at": None,
                    "created_at": "2023-01-01T00:00:00Z",
                    "source_sync_details": {"last_synced": "2024-01-01"},
                    "status": {
                        "sync_state": "syncing",
                        "setup_state": "connected",
                        "update_state": "on_schedule",
                        "is_historical_sync": False,
                        "rescheduled_for": None,
                        "schema_status": "ready",
                        "tasks": [
                            {
                                "code": "reconnect",
                                "message": "Reconnect required",
                                "details": "API key expired on 2024-01-15",
                            }
                        ],
                        "warnings": [
                            {
                                "code": "slow_sync",
                                "message": "Sync is slower than usual",
                                "details": "Last sync took 2x longer than average",
                            }
                        ],
                    },
                },
            },
        )
    )

    result = await _get_connection_status("conn_123")

    assert result["id"] == "conn_123"
    assert result["daily_sync_time"] == "03:00"
    assert result["data_delay_sensitivity"] == "NORMAL"
    assert result["source_sync_details"] == {"last_synced": "2024-01-01"}

    # Verify tasks include full details
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["code"] == "reconnect"
    assert result["tasks"][0]["details"] == "API key expired on 2024-01-15"

    # Verify warnings include full details
    assert len(result["warnings"]) == 1
    assert result["warnings"][0]["code"] == "slow_sync"
    assert result["warnings"][0]["details"] == "Last sync took 2x longer than average"


@pytest.mark.asyncio
async def test_get_schema_returns_schema_config(mock_env, mock_api):
    """Test get_schema returns schema configuration."""
    mock_api.get("/v1/connections/conn_123/schemas").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "schema_change_handling": "ALLOW_ALL",
                    "schemas": {
                        "public": {
                            "enabled": True,
                            "tables": {
                                "users": {"enabled": True},
                                "orders": {"enabled": False},
                            },
                        }
                    },
                },
            },
        )
    )

    result = await _get_schema("conn_123")

    assert result["connection_id"] == "conn_123"
    assert result["schema_change_handling"] == "ALLOW_ALL"
    assert "public" in result["schemas"]


@pytest.mark.asyncio
async def test_get_connection_schema_overview(mock_env, mock_api):
    """Test get_connection_schema returns schema overview without table filter."""
    mock_api.get("/v1/connections/conn_123/schemas").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "schema_change_handling": "ALLOW_COLUMNS",
                    "schemas": {
                        "public": {
                            "enabled": True,
                            "tables": {
                                "users": {"enabled": True},
                                "orders": {"enabled": True},
                            },
                        },
                        "analytics": {
                            "enabled": False,
                            "tables": {
                                "events": {"enabled": False},
                            },
                        },
                    },
                },
            },
        )
    )

    result = await _get_connection_schema("conn_123")

    assert result["connection_id"] == "conn_123"
    assert result["schema_change_handling"] == "ALLOW_COLUMNS"
    assert result["total_schemas"] == 2
    assert result["total_tables"] == 3
    assert result["enabled_tables"] == 2
    assert len(result["schemas"]) == 2


@pytest.mark.asyncio
async def test_get_connection_schema_with_table_filter(mock_env, mock_api):
    """Test get_connection_schema returns detailed table info with filter."""
    mock_api.get("/v1/connections/conn_123/schemas").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "schemas": {
                        "public": {
                            "enabled": True,
                            "tables": {
                                "users": {"enabled": True, "sync_mode": "SOFT_DELETE"},
                            },
                        }
                    },
                },
            },
        )
    )
    mock_api.get("/v1/connections/conn_123/schemas/public/tables/users/columns").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "columns": {
                        "id": {"enabled": True, "is_primary_key": True},
                        "email": {"enabled": True, "hashed": True},
                        "password": {"enabled": False},
                    }
                },
            },
        )
    )

    result = await _get_connection_schema("conn_123", table="public.users")

    assert result["connection_id"] == "conn_123"
    assert result["schema"] == "public"
    assert result["table"] == "users"
    assert result["full_name"] == "public.users"
    assert result["schema_enabled"] is True
    assert result["table_enabled"] is True
    assert result["sync_mode"] == "SOFT_DELETE"
    assert result["column_count"] == 3
    assert result["enabled_column_count"] == 2
    assert result["primary_keys"] == ["id"]


@pytest.mark.asyncio
async def test_get_connection_schema_invalid_table_format(mock_env, mock_api):
    """Test get_connection_schema handles invalid table format."""
    result = await _get_connection_schema("conn_123", table="invalid_format")

    assert "error" in result
    assert "invalid_format" in result["error"].lower()
    assert result["connection_id"] == "conn_123"


@pytest.mark.asyncio
async def test_list_tables_flattens_schema(mock_env, mock_api):
    """Test list_tables returns a flat list of all tables."""
    mock_api.get("/v1/connections/conn_123/schemas").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "schemas": {
                        "public": {
                            "enabled": True,
                            "tables": {
                                "users": {"enabled": True, "sync_mode": "SOFT_DELETE"},
                                "orders": {"enabled": False},
                            },
                        },
                        "analytics": {
                            "enabled": True,
                            "tables": {
                                "events": {"enabled": True, "sync_mode": "HISTORY"},
                            },
                        },
                    },
                },
            },
        )
    )

    result = await _list_tables("conn_123")

    assert result["connection_id"] == "conn_123"
    assert result["count"] == 3
    assert result["enabled_count"] == 2

    table_names = [t["full_name"] for t in result["tables"]]
    assert "public.users" in table_names
    assert "public.orders" in table_names
    assert "analytics.events" in table_names

    # Check table details
    users_table = next(t for t in result["tables"] if t["table"] == "users")
    assert users_table["enabled"] is True
    assert users_table["sync_mode"] == "SOFT_DELETE"
    assert users_table["schema_enabled"] is True


@pytest.mark.asyncio
async def test_get_table_columns_returns_column_details(mock_env, mock_api):
    """Test get_table_columns returns column information."""
    mock_api.get("/v1/connections/conn_123/schemas/public/tables/users/columns").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "columns": {
                        "id": {
                            "enabled": True,
                            "hashed": False,
                            "is_primary_key": True,
                            "name_in_destination": "user_id",
                        },
                        "email": {"enabled": True, "hashed": True},
                        "password": {
                            "enabled": False,
                            "hashed": True,
                            "enabled_patch_settings": {
                                "allowed": False,
                                "reason_code": "SYSTEM_COLUMN",
                            },
                        },
                    }
                },
            },
        )
    )

    result = await _get_table_columns("conn_123", "public", "users")

    assert result["connection_id"] == "conn_123"
    assert result["schema"] == "public"
    assert result["table"] == "users"
    assert result["column_count"] == 3
    assert result["enabled_count"] == 2
    assert result["primary_keys"] == ["id"]

    # Check column details
    id_col = next(c for c in result["columns"] if c["name"] == "id")
    assert id_col["is_primary_key"] is True
    assert id_col["hashed"] is False
    assert id_col["name_in_destination"] == "user_id"

    email_col = next(c for c in result["columns"] if c["name"] == "email")
    assert email_col["hashed"] is True

    password_col = next(c for c in result["columns"] if c["name"] == "password")
    assert password_col["enabled_patch_settings"]["reason_code"] == "SYSTEM_COLUMN"


@pytest.mark.asyncio
async def test_reload_schema_triggers_reload(mock_env, mock_api):
    """Test reload_schema triggers a schema reload."""
    mock_api.post("/v1/connections/conn_123/schemas/reload").mock(
        return_value=httpx.Response(
            200,
            json={"code": "Success", "message": "Schema reload triggered"},
        )
    )

    result = await _reload_schema("conn_123")

    assert result["success"] is True
    assert result["connection_id"] == "conn_123"
    assert "reload" in result["message"].lower()


@pytest.mark.asyncio
async def test_test_connection_returns_test_results(mock_env, mock_api):
    """Test test_connection returns formatted test results."""
    mock_api.post("/v1/connections/conn_123/test").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "setup_tests": [
                        {"title": "Host Connection", "status": "PASSED", "message": "Connected successfully"},
                        {"title": "Database Access", "status": "PASSED", "message": "Access granted"},
                        {"title": "Table Permissions", "status": "FAILED", "message": "Missing permissions", "details": "SELECT denied on users table"},
                    ]
                },
            },
        )
    )

    result = await _test_connection("conn_123")

    assert result["connection_id"] == "conn_123"
    assert result["overall_status"] == "FAILED"
    assert result["passed_count"] == 2
    assert result["failed_count"] == 1
    assert result["total_tests"] == 3

    failed_test = next(t for t in result["tests"] if t["status"] == "FAILED")
    assert failed_test["title"] == "Table Permissions"
    assert failed_test["details"] == "SELECT denied on users table"


@pytest.mark.asyncio
async def test_test_connection_all_passed(mock_env, mock_api):
    """Test test_connection shows PASSED when all tests pass."""
    mock_api.post("/v1/connections/conn_123/test").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "setup_tests": [
                        {"title": "Host Connection", "status": "PASSED", "message": "OK"},
                        {"title": "Database Access", "status": "PASSED", "message": "OK"},
                    ]
                },
            },
        )
    )

    result = await _test_connection("conn_123")

    assert result["overall_status"] == "PASSED"
    assert result["passed_count"] == 2
    assert result["failed_count"] == 0
