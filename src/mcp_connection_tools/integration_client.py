"""HTTP client for the Integration Manager API.

Self-contained async client for installing, uninstalling, listing,
restarting, and querying status of tenant MCP server integrations.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
DEFAULT_URL = "http://integration-manager.nb-control-plane:8080"


class IntegrationManagerClient:
    """Async HTTP client for the Integration Manager API."""

    def __init__(
        self,
        tenant_id: str,
        base_url: str = DEFAULT_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._tenant_id = tenant_id
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"X-Tenant-ID": self._tenant_id}

    async def install(
        self,
        package: str,
        version: str,
        credentials: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Install a tenant MCP server."""
        payload: dict[str, Any] = {"package": package, "version": version}
        if credentials:
            payload["credentials"] = credentials

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/v1/integrations",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def uninstall(self, server_name: str) -> None:
        """Uninstall a tenant MCP server."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.delete(
                f"{self._base_url}/v1/integrations/{server_name}",
                headers=self._headers(),
            )
            response.raise_for_status()

    async def list_integrations(self) -> list[dict[str, Any]]:
        """List all integrations for the tenant."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/v1/integrations",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_status(self, server_name: str) -> dict[str, Any]:
        """Get status of a specific integration."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/v1/integrations/{server_name}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def restart(self, server_name: str) -> None:
        """Restart a tenant MCP server."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/v1/integrations/{server_name}/restart",
                headers=self._headers(),
            )
            response.raise_for_status()
