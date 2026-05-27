> [!WARNING]
> **This repository is archived and no longer maintained.**
>
> This MCP server has been removed from the [mpak registry](https://mpak.dev).

---

# @nimblebraininc/connection-tools

MCP server registry search and integration management tools for AI agents.

## Tools

| Tool | Description |
|------|-------------|
| `registry_search` | Search the mpak registry for available MCP servers |
| `registry_resolve` | Get full metadata for a specific package |
| `integration_install` | Install an MCP server from the registry |
| `integration_uninstall` | Remove an installed MCP server |
| `integration_list` | List all installed integrations |
| `integration_status` | Get status of a specific integration |
| `integration_restart` | Restart a connected MCP server |

## Usage

### HTTP (platform service)

```bash
REGISTRY_URL=https://registry.mpak.dev \
INTEGRATION_MANAGER_URL=http://integration-manager:8080 \
uvicorn mcp_connection_tools.server:app --host 0.0.0.0 --port 8080
```

### Docker

```bash
docker build -t connection-tools .
docker run -p 8080:8080 \
  -e REGISTRY_URL=https://registry.mpak.dev \
  -e INTEGRATION_MANAGER_URL=http://integration-manager:8080 \
  connection-tools
```

### mpak

```bash
mpak install @nimblebraininc/connection-tools
```

## Configuration

| Env Var | Required | Description |
|---------|----------|-------------|
| `REGISTRY_URL` | No | mpak registry URL (default: https://registry.mpak.dev) |
| `INTEGRATION_MANAGER_URL` | No | Integration Manager service URL |
| `TENANT_ID` | No | Tenant identifier (default: "default") |

## Development

```bash
make dev-install
make test
make check
```

## License

MIT
