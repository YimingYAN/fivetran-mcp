# Fivetran MCP Server

An MCP (Model Context Protocol) server for controlling Fivetran syncs. Enables AI assistants to manage data pipelines, trigger syncs, and monitor connection status.

## Features

- **List connections** - View all Fivetran connections with status
- **Check sync status** - Get detailed status for any connection
- **Trigger syncs** - Start syncs on demand
- **Historical resync** - Trigger full data resync or resync specific tables
- **Pause/Resume** - Control connection scheduling
- **List groups** - View all destination groups

## Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/YimingYAN/fivetran-mcp.git
cd fivetran-mcp
uv sync
```

### Step 2: Get Fivetran API Credentials

1. Log in to [Fivetran Dashboard](https://fivetran.com/dashboard)
2. Click your **username** (top right corner)
3. Click **API Key**
4. Click **Generate API key**
5. Copy both the **API Key** and **API Secret** (secret shown only once!)

See [Fivetran API Getting Started](https://fivetran.com/docs/rest-api/getting-started) for more details.

### Step 3: Store Credentials

Add to your `~/.env.local` (or equivalent):

```bash
# Fivetran API
export FIVETRAN_SYNC_API_KEY="your-api-key"
export FIVETRAN_SYNC_API_SECRET="your-api-secret"
```

Then reload:
```bash
source ~/.env.local
```

### Step 4: Verify Credentials

Test that your credentials work:

```bash
curl -s -X GET "https://api.fivetran.com/v1/account/info" \
  -H "Accept: application/json" \
  -H "Authorization: Basic $(echo -n "$FIVETRAN_SYNC_API_KEY:$FIVETRAN_SYNC_API_SECRET" | base64)"
```

Expected response:
```json
{"code":"Success","data":{"account_id":"...","account_name":"..."}}
```

### Step 5: Configure Claude Code

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

Replace `/path/to/fivetran-mcp` with the actual path (e.g., `~/Playground/fivetran-mcp`).

### Step 6: Restart Claude Code

Restart Claude Code to load the new MCP server. You should now have access to Fivetran tools.

## Available Tools

| Tool | Description |
|------|-------------|
| `list_connections` | List all connections, optionally filtered by group |
| `get_connection_status` | Get detailed status for a connection |
| `trigger_sync` | Start a sync for a connection (optional `force` flag) |
| `trigger_resync` | Trigger full historical resync |
| `resync_tables` | Resync specific tables only (e.g., `["schema.table_name"]`) |
| `pause_connection` | Pause a connection |
| `resume_connection` | Resume a paused connection |
| `list_groups` | List all groups/destinations |

## Environment Variables

The server supports two naming conventions:

| Preferred | Alternative |
|-----------|-------------|
| `FIVETRAN_SYNC_API_KEY` | `FIVETRAN_API_KEY` |
| `FIVETRAN_SYNC_API_SECRET` | `FIVETRAN_API_SECRET` |

## Development

```bash
# Install dependencies
uv sync

# Run the server locally
uv run fivetran-mcp
```

## License

MIT
