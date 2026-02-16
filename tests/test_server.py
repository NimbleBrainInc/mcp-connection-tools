"""Tests for the connection-tools MCP server.

Uses FastMCP test client with mocked HTTP backends.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from mcp_connection_tools.server import mcp


@pytest.fixture(autouse=True)
def reset_clients():
    """Reset lazy-initialized clients between tests."""
    import mcp_connection_tools.server as srv

    srv._registry_client = None
    srv._integration_client = None


@pytest.fixture
def mcp_server():
    """Return the MCP server instance."""
    return mcp


@pytest.mark.asyncio
async def test_tools_list(mcp_server):
    """Test that all 7 tools are registered."""
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]
        assert "registry_search" in tool_names
        assert "registry_resolve" in tool_names
        assert "integration_install" in tool_names
        assert "integration_uninstall" in tool_names
        assert "integration_list" in tool_names
        assert "integration_status" in tool_names
        assert "integration_restart" in tool_names
        assert len(tool_names) == 7


@pytest.mark.asyncio
async def test_registry_search(mcp_server, monkeypatch):
    """Test registry search with mocked client."""
    mock_results = [
        {
            "name": "@nimblebraininc/finnhub",
            "display_name": "Finnhub",
            "description": "Financial data",
            "latest_version": "0.1.0",
            "server_type": "python",
            "tools": [{"name": "get_quote", "description": "Get stock quote"}],
            "downloads": 100,
            "verified": True,
            "certification_level": None,
        }
    ]

    mock_search = AsyncMock(return_value=mock_results)
    with patch(
        "mcp_connection_tools.server._get_registry_client"
    ) as mock_get:
        mock_client = AsyncMock()
        mock_client.search = mock_search
        mock_get.return_value = mock_client

        with patch(
            "mcp_connection_tools.server._get_integration_client",
            return_value=None,
        ):
            async with Client(mcp_server) as client:
                result = await client.call_tool("registry_search", {"query": "finance"})
                result_str = str(result)
                assert "finnhub" in result_str


@pytest.mark.asyncio
async def test_registry_resolve(mcp_server):
    """Test registry resolve with mocked client."""
    mock_result = {
        "name": "@nimblebraininc/finnhub",
        "display_name": "Finnhub",
        "description": "Financial data",
        "version": "0.1.0",
        "tools": [],
        "credential_type": "api_key",
        "credentials_required": [{"name": "FINNHUB_API_KEY", "description": "API key"}],
        "homepage": None,
        "license": "MIT",
        "verified": True,
    }

    with patch(
        "mcp_connection_tools.server._get_registry_client"
    ) as mock_get:
        mock_client = AsyncMock()
        mock_client.resolve = AsyncMock(return_value=mock_result)
        mock_get.return_value = mock_client

        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "registry_resolve",
                {"package": "@nimblebraininc/finnhub"},
            )
            result_str = str(result)
            assert "finnhub" in result_str


@pytest.mark.asyncio
async def test_integration_install_not_configured(mcp_server):
    """Test integration_install when Integration Manager is not configured."""
    with patch(
        "mcp_connection_tools.server._get_integration_client",
        return_value=None,
    ):
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "integration_install",
                {"package": "@nimblebraininc/finnhub", "version": "0.1.0"},
            )
            result_str = str(result)
            assert "not configured" in result_str.lower() or "error" in result_str.lower()


@pytest.mark.asyncio
async def test_integration_list_not_configured(mcp_server):
    """Test integration_list when Integration Manager is not configured."""
    with patch(
        "mcp_connection_tools.server._get_integration_client",
        return_value=None,
    ):
        async with Client(mcp_server) as client:
            result = await client.call_tool("integration_list", {})
            result_str = str(result)
            assert "not configured" in result_str.lower() or "error" in result_str.lower()
