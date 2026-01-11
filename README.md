# Fivetran MCP Server

An MCP (Model Context Protocol) server for controlling Fivetran syncs. Enables AI assistants to manage data pipelines, trigger syncs, and monitor connection status.

## Features

- **List connections** - View all Fivetran connections with status
- **Check sync status** - Get detailed status for any connection
- **Trigger syncs** - Start syncs on demand
- **Historical resync** - Trigger full data resync
- **Pause/Resume** - Control connection scheduling
- **List groups** - View all destination groups

## Installation

```bash
# Using uv
uv add fivetran-mcp

# Or install from source
git clone <repo>
cd fivetran-mcp
uv sync
```

## Configuration

Set the following environment variables:

```bash
export FIVETRAN_API_KEY="your-api-key"
export FIVETRAN_API_SECRET="your-api-secret"
```

You can generate API credentials in the Fivetran dashboard under Settings > API Config.

## Usage with Claude Code

Add to your `~/.claude.json`:

```json
{
  "mcpServers": {
    "fivetran": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/fivetran-mcp", "fivetran-mcp"],
      "env": {
        "FIVETRAN_API_KEY": "${FIVETRAN_API_KEY}",
        "FIVETRAN_API_SECRET": "${FIVETRAN_API_SECRET}"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_connections` | List all connections, optionally filtered by group |
| `get_connection_status` | Get detailed status for a connection |
| `trigger_sync` | Start a sync for a connection |
| `trigger_resync` | Trigger historical resync |
| `pause_connection` | Pause a connection |
| `resume_connection` | Resume a paused connection |
| `list_groups` | List all groups/destinations |

## Development

```bash
# Install dependencies
uv sync

# Run the server locally
uv run fivetran-mcp
```

## License

MIT
