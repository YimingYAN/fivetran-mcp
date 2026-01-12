"""Pytest fixtures for Fivetran MCP tests."""

import pytest
import respx


@pytest.fixture
def mock_api():
    """Fixture that provides a respx mock for Fivetran API calls."""
    with respx.mock(base_url="https://api.fivetran.com") as respx_mock:
        yield respx_mock
