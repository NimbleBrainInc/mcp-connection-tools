"""Connection Tools MCP Server.

MCP server registry search and integration management tools for AI agents.
Wraps HTTP calls to the mpak registry and Integration Manager service.

Designed to run as an HTTP MCP server in the nb-platform namespace,
shared across all tenants.

Environment variables:
    REGISTRY_URL: mpak registry URL (default: https://registry.mpak.dev).
    INTEGRATION_MANAGER_URL: Integration Manager service URL (required for install/uninstall).
    TENANT_ID: Tenant identifier (injected per-request in production via X-Tenant-ID header).
"""

import logging
import os
import sys
from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .integration_client import IntegrationManagerClient
from .registry_client import RegistrySearchClient

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_connection_tools")

mcp = FastMCP(
    "connection-tools",
    instructions=(
        "Before searching or installing MCP servers, read the "
        "skill://connection-tools/usage resource for workflow guidance."
    ),
)

# ---------------------------------------------------------------------------
# Lazy client initialization
# ---------------------------------------------------------------------------

_registry_client: RegistrySearchClient | None = None
_integration_client: IntegrationManagerClient | None = None


def _get_registry_client() -> RegistrySearchClient:
    """Lazily initialize the registry client."""
    global _registry_client
    if _registry_client is None:
        url = os.environ.get("REGISTRY_URL", "https://registry.mpak.dev")
        _registry_client = RegistrySearchClient(registry_url=url)
        logger.info("Initialized RegistrySearchClient at %s", url)
    return _registry_client


def _get_integration_client() -> IntegrationManagerClient | None:
    """Lazily initialize the integration client (may not be configured)."""
    global _integration_client
    if _integration_client is None:
        url = os.environ.get("INTEGRATION_MANAGER_URL")
        if url:
            tenant_id = os.environ.get("TENANT_ID", "default")
            _integration_client = IntegrationManagerClient(
                tenant_id=tenant_id, base_url=url
            )
            logger.info("Initialized IntegrationManagerClient at %s", url)
    return _integration_client


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for K8s probes."""
    return JSONResponse({"status": "healthy", "service": "mcp-connection-tools"})


# ---------------------------------------------------------------------------
# Registry tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def registry_search(query: str) -> dict[str, Any]:
    """Search the mpak registry for available MCP servers to connect.

    Returns name, description, tools, and whether already installed.

    Args:
        query: Search term (e.g., 'weather', 'pdf', 'finance').

    Returns:
        Search results with count and query.
    """
    client = _get_registry_client()
    results = await client.search(query)

    # Cross-reference with installed integrations
    installed_names: set[str] = set()
    im_client = _get_integration_client()
    if im_client is not None:
        try:
            integrations = await im_client.list_integrations()
            installed_names = {i["server_name"] for i in integrations}
        except Exception:
            pass  # Non-fatal

    for r in results:
        name = r["name"]
        server_name = name.rsplit("/", 1)[-1] if "/" in name else name
        r["installed"] = server_name in installed_names

    return {
        "results": results,
        "count": len(results),
        "query": query,
    }


@mcp.tool()
async def registry_resolve(package: str, version: str | None = None) -> dict[str, Any]:
    """Get full metadata for a specific package from the mpak registry.

    Includes credential requirements and available tools.

    Args:
        package: Package identifier (e.g., '@nimblebrain/finnhub').
        version: Specific version. Omit for latest.

    Returns:
        Package metadata dict.
    """
    client = _get_registry_client()
    return await client.resolve(package, version)


# ---------------------------------------------------------------------------
# Integration tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def integration_install(
    package: str,
    version: str,
    credentials: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Install an MCP server from the mpak registry.

    If the server requires an API key, provide it in credentials.
    If credentials are unknown, call without them to see what's needed.

    Args:
        package: Package identifier (e.g., '@nimblebrain/finnhub').
        version: Version (e.g., '0.1.0').
        credentials: API keys/secrets as key-value pairs.

    Returns:
        Integration response with server_name, phase, tools, endpoint.
    """
    client = _get_integration_client()
    if client is None:
        raise RuntimeError("Integration Manager not configured (INTEGRATION_MANAGER_URL not set)")
    return await client.install(package, version, credentials)


@mcp.tool()
async def integration_uninstall(server_name: str) -> dict[str, Any]:
    """Disconnect and remove an MCP server. Deletes credentials and stops the server.

    Args:
        server_name: Server name (e.g., 'finnhub').

    Returns:
        Confirmation dict.
    """
    client = _get_integration_client()
    if client is None:
        raise RuntimeError("Integration Manager not configured (INTEGRATION_MANAGER_URL not set)")
    await client.uninstall(server_name)
    return {"server_name": server_name, "status": "uninstalled"}


@mcp.tool()
async def integration_list() -> dict[str, Any]:
    """List all installed MCP server integrations with their status, tools, and endpoints.

    Returns:
        Dict with integrations list and count.
    """
    client = _get_integration_client()
    if client is None:
        raise RuntimeError("Integration Manager not configured (INTEGRATION_MANAGER_URL not set)")
    integrations = await client.list_integrations()
    return {
        "integrations": integrations,
        "count": len(integrations),
    }


@mcp.tool()
async def integration_status(server_name: str) -> dict[str, Any]:
    """Get the current status and health of a specific installed integration.

    Args:
        server_name: Server name (e.g., 'finnhub').

    Returns:
        Integration status dict.
    """
    client = _get_integration_client()
    if client is None:
        raise RuntimeError("Integration Manager not configured (INTEGRATION_MANAGER_URL not set)")
    return await client.get_status(server_name)


@mcp.tool()
async def integration_restart(server_name: str) -> dict[str, Any]:
    """Restart a connected MCP server. Use when a server is unresponsive or in an error state.

    Args:
        server_name: Server name to restart (e.g., 'finnhub').

    Returns:
        Confirmation dict.
    """
    client = _get_integration_client()
    if client is None:
        raise RuntimeError("Integration Manager not configured (INTEGRATION_MANAGER_URL not set)")
    await client.restart(server_name)
    return {"server_name": server_name, "status": "restarting"}


# ---------------------------------------------------------------------------
# SKILL.md resource
# ---------------------------------------------------------------------------

from importlib.resources import files

try:
    SKILL_CONTENT = files("mcp_connection_tools").joinpath("SKILL.md").read_text()
except FileNotFoundError:
    SKILL_CONTENT = "Connection tools for registry search and integration management."


@mcp.resource("skill://connection-tools/usage")
def connection_tools_skill() -> str:
    """How to effectively use connection tools."""
    return SKILL_CONTENT


# ---------------------------------------------------------------------------
# Entrypoints
# ---------------------------------------------------------------------------

app = mcp.http_app()

if __name__ == "__main__":
    logger.info("Running in stdio mode")
    mcp.run()
