# Fivetran MCP Server

An MCP (Model Context Protocol) server for controlling Fivetran syncs. Enables AI assistants to manage data pipelines, trigger syncs, and monitor connection status.

## Features

- **List connections** - View all Fivetran connections with status
- **Check sync status** - Get detailed status for any connection
- **Trigger syncs** - Start syncs on demand
- **Historical resync** - Trigger full data resync or resync specific tables
- **Pause/Resume** - Control connection scheduling
- **List groups** - View all destination groups

## Installation

```bash
# Install from source
git clone https://github.com/YimingYAN/fivetran-mcp.git
cd fivetran-mcp
uv sync
```

## Configuration

### Getting API Credentials

1. Go to Fivetran Dashboard → Click your username → **API Key**
2. Click **Generate API key**
3. Save both the API Key and API Secret securely

See [Fivetran API Getting Started](https://fivetran.com/docs/rest-api/getting-started) for details.

### Environment Variables

Set the following environment variables (supports both naming conventions):

```bash
# Preferred (matches eunice-data convention)
export FIVETRAN_SYNC_API_KEY="your-api-key"
export FIVETRAN_SYNC_API_SECRET="your-api-secret"

# Alternative
export FIVETRAN_API_KEY="your-api-key"
export FIVETRAN_API_SECRET="your-api-secret"
```

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
        "FIVETRAN_SYNC_API_KEY": "${FIVETRAN_SYNC_API_KEY}",
        "FIVETRAN_SYNC_API_SECRET": "${FIVETRAN_SYNC_API_SECRET}"
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
| `trigger_resync` | Trigger full historical resync |
| `resync_tables` | Resync specific tables only (e.g., `["schema.table_name"]`) |
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
