# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

Fivetran MCP Server is a Python-based MCP (Model Context Protocol) server that exposes Fivetran API operations as tools for AI assistants. It enables AI assistants like Claude to manage data syncs, monitor connection status, and control Fivetran data pipelines through natural language.

## Architecture

- **`src/fivetran_mcp/server.py`**: MCP server implementation using FastMCP. Defines all exposed tools (`list_connections`, `get_connection_status`, `trigger_sync`, `trigger_resync`, `resync_tables`, `pause_connection`, `resume_connection`, `list_groups`).
- **`src/fivetran_mcp/client.py`**: Async HTTP client for the Fivetran REST API using httpx. Handles authentication and API request/response logic.

## Development Commands

```bash
# Install dependencies
uv sync

# Run the MCP server locally
uv run fivetran-mcp
```

## Environment Variables

The server requires Fivetran API credentials. Both naming conventions are supported:

| Preferred                    | Alternative            |
|------------------------------|------------------------|
| `FIVETRAN_SYNC_API_KEY`      | `FIVETRAN_API_KEY`     |
| `FIVETRAN_SYNC_API_SECRET`   | `FIVETRAN_API_SECRET`  |

## Key Dependencies

- **fastmcp** (>=2.0.0): FastMCP framework for building MCP servers
- **httpx** (>=0.28.0): Async HTTP client for API requests
- Python 3.10+

## Code Style

- Async/await patterns for all API operations
- Type hints throughout (Python typing module)
- Docstrings with Args/Returns sections for all public functions
- Module-level singleton pattern for the FivetranClient instance
