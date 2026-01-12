"""Tests for Fivetran API client."""

import httpx
import pytest
import respx

from fivetran_mcp.fivetran_api import FivetranAPIError, FivetranClient


@pytest.fixture
def client():
    """Create a Fivetran client for testing."""
    return FivetranClient(api_key="test_key", api_secret="test_secret")


@pytest.mark.asyncio
async def test_api_error_extracts_message(client, mock_api):
    """Test that API errors include the message from Fivetran's response."""
    mock_api.post("/v1/connections/invalid_id/test").mock(
        return_value=httpx.Response(
            400,
            json={
                "code": "BadRequest",
                "message": "Connection 'invalid_id' not found",
            },
        )
    )

    with pytest.raises(FivetranAPIError) as exc_info:
        await client.test_connection("invalid_id")

    assert exc_info.value.status_code == 400
    assert "Connection 'invalid_id' not found" in exc_info.value.message
    assert "Connection 'invalid_id' not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_api_error_handles_non_json_response(client, mock_api):
    """Test that API errors handle non-JSON responses gracefully."""
    mock_api.post("/v1/connections/broken/test").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    with pytest.raises(FivetranAPIError) as exc_info:
        await client.test_connection("broken")

    assert exc_info.value.status_code == 500
    assert "Internal Server Error" in exc_info.value.message


@pytest.mark.asyncio
async def test_api_error_handles_empty_response(client, mock_api):
    """Test that API errors handle empty responses gracefully."""
    mock_api.post("/v1/connections/empty/test").mock(
        return_value=httpx.Response(404, text="")
    )

    with pytest.raises(FivetranAPIError) as exc_info:
        await client.test_connection("empty")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_connection_success(client, mock_api):
    """Test successful get_connection call."""
    mock_api.get("/v1/connections/conn_123").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "id": "conn_123",
                    "schema": "test_schema",
                    "service": "postgres",
                    "status": {
                        "sync_state": "syncing",
                        "setup_state": "connected",
                    },
                },
            },
        )
    )

    result = await client.get_connection("conn_123")
    assert result["data"]["id"] == "conn_123"
    assert result["data"]["status"]["sync_state"] == "syncing"


@pytest.mark.asyncio
async def test_get_schema_success(client, mock_api):
    """Test successful get_schema call."""
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
                                "users": {"enabled": True, "sync_mode": "SOFT_DELETE"},
                                "orders": {"enabled": False},
                            },
                        }
                    },
                },
            },
        )
    )

    result = await client.get_schema("conn_123")
    assert result["data"]["schema_change_handling"] == "ALLOW_ALL"
    assert "public" in result["data"]["schemas"]
    assert result["data"]["schemas"]["public"]["tables"]["users"]["enabled"] is True


@pytest.mark.asyncio
async def test_get_table_columns_success(client, mock_api):
    """Test successful get_table_columns call."""
    mock_api.get("/v1/connections/conn_123/schemas/public/tables/users/columns").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "columns": {
                        "id": {"enabled": True, "hashed": False, "is_primary_key": True},
                        "email": {"enabled": True, "hashed": True},
                        "name": {"enabled": True, "hashed": False},
                    }
                },
            },
        )
    )

    result = await client.get_table_columns("conn_123", "public", "users")
    assert "id" in result["data"]["columns"]
    assert result["data"]["columns"]["id"]["is_primary_key"] is True
    assert result["data"]["columns"]["email"]["hashed"] is True


@pytest.mark.asyncio
async def test_reload_schema_success(client, mock_api):
    """Test successful reload_schema call."""
    mock_api.post("/v1/connections/conn_123/schemas/reload").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "message": "Schema reload triggered",
            },
        )
    )

    result = await client.reload_schema("conn_123")
    assert result["code"] == "Success"


@pytest.mark.asyncio
async def test_test_connection_success(client, mock_api):
    """Test successful test_connection call."""
    mock_api.post("/v1/connections/conn_123/test").mock(
        return_value=httpx.Response(
            200,
            json={
                "code": "Success",
                "data": {
                    "setup_tests": [
                        {"title": "Host Connection", "status": "PASSED", "message": "OK"},
                        {"title": "Database Connection", "status": "PASSED", "message": "OK"},
                    ]
                },
            },
        )
    )

    result = await client.test_connection("conn_123")
    assert len(result["data"]["setup_tests"]) == 2
    assert result["data"]["setup_tests"][0]["status"] == "PASSED"
