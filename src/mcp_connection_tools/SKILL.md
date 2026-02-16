# Connection Tools

## Tool Selection

| Intent | Tool |
|--------|------|
| Find available MCP servers | `registry_search(query)` |
| Get package details/requirements | `registry_resolve(package, version?)` |
| Install an MCP server | `integration_install(package, version, credentials?)` |
| Remove an MCP server | `integration_uninstall(server_name)` |
| List installed integrations | `integration_list()` |
| Check integration health | `integration_status(server_name)` |
| Restart a stuck server | `integration_restart(server_name)` |

## Multi-Step Workflows

### Install a new MCP server
1. `registry_search(query)` to find matching servers
2. `registry_resolve(package)` to check credential requirements
3. Ask user for API key if needed
4. `integration_install(package, version, credentials)` to install
5. Wait for the server to become available (tools appear in next turn)

### Troubleshoot an integration
1. `integration_status(server_name)` to check health
2. If unhealthy, `integration_restart(server_name)`
3. If still failing, `integration_uninstall(server_name)` and reinstall

## Key Patterns

- Always call `registry_resolve` before `integration_install` to discover credential requirements.
- If credentials are unknown, call `integration_install` without them to see what's needed.
- After install/uninstall, the agent will automatically re-discover available tools.
