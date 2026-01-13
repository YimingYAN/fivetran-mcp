"""Fivetran API client using httpx."""

import base64
from typing import Any

import httpx


class FivetranAPIError(Exception):
    """Fivetran API error with status code and detailed message."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Fivetran API error ({status_code}): {message}")


class FivetranClient:
    """Async HTTP client for Fivetran REST API."""

    BASE_URL = "https://api.fivetran.com"

    def __init__(self, api_key: str, api_secret: str) -> None:
        credentials = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def list_connections(
        self, limit: int = 100, cursor: str | None = None
    ) -> dict[str, Any]:
        """List all connections in the account."""
        return await self._request(
            "GET", "/v1/connections", params=_pagination_params(limit, cursor)
        )

    async def get_connection(self, connection_id: str) -> dict[str, Any]:
        """Get details for a specific connection."""
        return await self._request("GET", f"/v1/connections/{connection_id}")

    async def trigger_sync(
        self, connection_id: str, force: bool = False
    ) -> dict[str, Any]:
        """Trigger a sync for a connection."""
        return await self._request(
            "POST",
            f"/v1/connections/{connection_id}/sync",
            json={"force": force},
        )

    async def trigger_resync(
        self, connection_id: str, scope: dict[str, list[str]] | None = None
    ) -> dict[str, Any]:
        """Trigger a historical resync for a connection."""
        json_body = {"scope": scope} if scope else None
        return await self._request(
            "POST",
            f"/v1/connections/{connection_id}/resync",
            json=json_body,
        )

    async def update_connection(
        self, connection_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a connection's settings."""
        return await self._request(
            "PATCH",
            f"/v1/connections/{connection_id}",
            json=updates,
        )

    async def pause_connection(self, connection_id: str) -> dict[str, Any]:
        """Pause a connection."""
        return await self.update_connection(connection_id, {"paused": True})

    async def resume_connection(self, connection_id: str) -> dict[str, Any]:
        """Resume a paused connection."""
        return await self.update_connection(connection_id, {"paused": False})

    async def list_groups(
        self, limit: int = 100, cursor: str | None = None
    ) -> dict[str, Any]:
        """List all groups in the account."""
        return await self._request(
            "GET", "/v1/groups", params=_pagination_params(limit, cursor)
        )

    async def list_connections_in_group(
        self, group_id: str, limit: int = 100, cursor: str | None = None
    ) -> dict[str, Any]:
        """List connections within a specific group."""
        return await self._request(
            "GET",
            f"/v1/groups/{group_id}/connections",
            params=_pagination_params(limit, cursor),
        )

    async def resync_tables(
        self, connection_id: str, tables: list[str]
    ) -> dict[str, Any]:
        """Trigger a historical resync for specific tables within a connection.

        Args:
            connection_id: The connection identifier
            tables: List of table names in format "schema.table" (e.g., ["public.users"])
        """
        return await self._request(
            "POST",
            f"/v1/connections/{connection_id}/schemas/tables/resync",
            json={"schema": tables},
        )

    async def test_connection(self, connection_id: str) -> dict[str, Any]:
        """Test a connection to diagnose connectivity and configuration issues.

        Args:
            connection_id: The connection identifier

        Returns:
            Dictionary containing test results with overall status and individual test details
        """
        return await self._request(
            "POST",
            f"/v1/connections/{connection_id}/test",
        )

    async def get_schema(self, connection_id: str) -> dict[str, Any]:
        """Retrieve the schema configuration for a connection.

        Returns the complete schema config including all schemas, tables, and their
        enabled/disabled status.

        Args:
            connection_id: The connection identifier

        Returns:
            Dictionary containing schema configuration with tables and their sync status
        """
        return await self._request("GET", f"/v1/connections/{connection_id}/schemas")

    async def get_table_columns(
        self, connection_id: str, schema: str, table: str
    ) -> dict[str, Any]:
        """Retrieve column configuration for a specific table.

        Args:
            connection_id: The connection identifier
            schema: The schema name
            table: The table name

        Returns:
            Dictionary containing column details including names, types, and enabled status
        """
        return await self._request(
            "GET",
            f"/v1/connections/{connection_id}/schemas/{schema}/tables/{table}/columns",
        )

    async def reload_schema(self, connection_id: str) -> dict[str, Any]:
        """Reload the schema configuration from the source.

        Fetches the latest schema from the source and updates the configuration.
        Useful after source schema changes.

        Args:
            connection_id: The connection identifier

        Returns:
            Dictionary containing the updated schema configuration
        """
        return await self._request(
            "POST",
            f"/v1/connections/{connection_id}/schemas/reload",
        )

    async def get_connector_logs(
        self, connection_id: str, limit: int = 100, cursor: str | None = None
    ) -> dict[str, Any]:
        """Retrieve sync logs for a connection.

        Fetches sync history including timestamps, error messages, and sync details.
        Note: This endpoint may not be available for all Fivetran accounts.

        Args:
            connection_id: The connection identifier
            limit: Maximum number of log entries to return (default 100)
            cursor: Pagination cursor for fetching additional results

        Returns:
            Dictionary containing log entries with sync history and error details

        Raises:
            FivetranAPIError: If the endpoint is not available or returns an error
        """
        params = _pagination_params(limit, cursor)
        return await self._request(
            "GET",
            f"/v1/connectors/{connection_id}/logs",
            params=params,
        )

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request and return the JSON response.

        Raises:
            FivetranAPIError: When the API returns an error response with details
        """
        response = await self._client.request(method, path, params=params, json=json)

        if not response.is_success:
            # Extract error message from Fivetran's response body
            try:
                error_data = response.json()
                error_msg = error_data.get("message", str(error_data))
            except Exception:
                error_msg = response.text or response.reason_phrase or "Unknown error"
            raise FivetranAPIError(response.status_code, error_msg)

        return response.json()


def _pagination_params(limit: int, cursor: str | None) -> dict[str, Any]:
    """Build pagination parameters for API requests."""
    params: dict[str, Any] = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    return params
