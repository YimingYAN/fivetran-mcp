# Fivetran MCP Server

[![PyPI version](https://img.shields.io/pypi/v/fivetran-mcp.svg)](https://pypi.org/project/fivetran-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built by Claude Code](https://img.shields.io/badge/Built%20by-Claude%20Code-blueviolet)](https://claude.ai/code)

> **Note:** This repository is built and maintained entirely by [Claude Code](https://claude.ai/code), Anthropic's AI coding assistant.

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server for controlling [Fivetran](https://fivetran.com/) data pipelines. Enables AI assistants like Claude to manage syncs, monitor connection status, and control data pipelines through natural language.

## Features

- **List connections** - View all Fivetran connections with status
- **Check sync status** - Get detailed status for any connection
- **Trigger syncs** - Start syncs on demand
- **Historical resync** - Trigger full data resync or resync specific tables
- **Pause/Resume** - Control connection scheduling
- **List groups** - View all destination groups
- **Test connection** - Diagnose connectivity and configuration issues

## Quick Start

### Step 1: Get Fivetran API Credentials

1. Log in to [Fivetran Dashboard](https://fivetran.com/dashboard)
2. Click your **username** (top right corner)
3. Click **API Key**
4. Click **Generate API key**
5. Copy both the **API Key** and **API Secret** (secret shown only once!)

See [Fivetran API Getting Started](https://fivetran.com/docs/rest-api/getting-started) for more details.

### Step 2: Store Credentials

Add to your `~/.env.local` (or equivalent):

```bash
# Fivetran API
export FIVETRAN_API_KEY="your-api-key"
export FIVETRAN_API_SECRET="your-api-secret"
```

Then reload:
```bash
source ~/.env.local
```

### Step 3: Verify Credentials

Test that your credentials work:

```bash
curl -s -X GET "https://api.fivetran.com/v1/account/info" \
  -H "Accept: application/json" \
  -H "Authorization: Basic $(echo -n "$FIVETRAN_API_KEY:$FIVETRAN_API_SECRET" | base64)"
```

Expected response:
```json
{"code":"Success","data":{"account_id":"...","account_name":"..."}}
```

### Step 4: Configure Claude Code

Add to your `~/.claude.json`:

```json
{
  "mcpServers": {
    "fivetran": {
      "type": "stdio",
      "command": "uvx",
      "args": ["fivetran-mcp@latest"],
      "env": {
        "FIVETRAN_API_KEY": "${FIVETRAN_API_KEY}",
        "FIVETRAN_API_SECRET": "${FIVETRAN_API_SECRET}"
      }
    }
  }
}
```

### Step 5: Restart Claude Code

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
| `test_connection` | Run diagnostic tests to identify connectivity/configuration issues |

## Environment Variables

The server supports two naming conventions:

| Preferred | Alternative |
|-----------|-------------|
| `FIVETRAN_API_KEY` | `FIVETRAN_SYNC_API_KEY` |
| `FIVETRAN_API_SECRET` | `FIVETRAN_SYNC_API_SECRET` |

## Development

```bash
# Clone the repository
git clone https://github.com/YimingYAN/fivetran-mcp.git
cd fivetran-mcp

# Install dependencies
uv sync

# Run the server locally
uv run fivetran-mcp
```

## License

[MIT](LICENSE)
