"""Fivetran API client using httpx."""

import base64
from typing import Any

import httpx


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

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request and return the JSON response."""
        response = await self._client.request(method, path, params=params, json=json)
        response.raise_for_status()
        return response.json()

    async def list_connections(
        self, limit: int = 100, cursor: str | None = None
    ) -> dict[str, Any]:
        """List all connections in the account."""
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return await self._request("GET", "/v1/connections", params=params)

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
        json_body: dict[str, Any] = {}
        if scope:
            json_body["scope"] = scope
        return await self._request(
            "POST",
            f"/v1/connections/{connection_id}/resync",
            json=json_body if json_body else None,
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
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return await self._request("GET", "/v1/groups", params=params)

    async def list_connections_in_group(
        self, group_id: str, limit: int = 100, cursor: str | None = None
    ) -> dict[str, Any]:
        """List connections within a specific group."""
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return await self._request(
            "GET", f"/v1/groups/{group_id}/connections", params=params
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
