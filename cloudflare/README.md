# Cloudflare Workers Deployment

Deploy the Fivetran MCP Server on Cloudflare Workers (free tier).

> **Note:** Cloudflare Python Workers are in beta. Some features may change.

## Prerequisites

- [Cloudflare account](https://dash.cloudflare.com/sign-up) (free)
- [uv](https://github.com/astral-sh/uv) installed
- Node.js 18+ installed

## Setup

```bash
cd cloudflare

# Install workers-py
uv tool install workers-py

# Initialize (if not already done)
uv run pywrangler init
```

## Configure Secrets

Set your Fivetran API credentials:

```bash
# Login to Cloudflare
npx wrangler login

# Set secrets
npx wrangler secret put FIVETRAN_API_KEY
# Enter your API key when prompted

npx wrangler secret put FIVETRAN_API_SECRET
# Enter your API secret when prompted
```

## Local Development

```bash
uv run pywrangler dev
# Server runs at http://localhost:8788
```

Test the endpoints:

```bash
# Health check
curl http://localhost:8788/

# List tools
curl http://localhost:8788/tools

# Execute a tool
curl -X POST http://localhost:8788/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_connections", "arguments": {"limit": 10}}'
```

## Deploy

```bash
uv run pywrangler deploy
```

Your server will be available at: `https://fivetran-mcp.<your-account>.workers.dev`

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/mcp` | GET | MCP server info |
| `/tools` | GET | List available tools |
| `/execute` | POST | Execute a tool |

## Usage with MCP Clients

### Claude Desktop (via mcp-remote)

```json
{
  "mcpServers": {
    "fivetran": {
      "command": "npx",
      "args": ["mcp-remote", "https://fivetran-mcp.<your-account>.workers.dev/mcp"]
    }
  }
}
```

### Direct HTTP

```bash
curl -X POST https://fivetran-mcp.<your-account>.workers.dev/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "list_groups", "arguments": {}}'
```

## Free Tier Limits

Cloudflare Workers free tier includes:
- 100,000 requests/day
- 10ms CPU time per request
- No credit card required

For most MCP use cases, this is more than sufficient.

## Limitations

1. **Beta status**: Python Workers are in beta
2. **No persistent state**: Each request is stateless
3. **CPU time limit**: Long-running operations may timeout

For production workloads requiring more reliability, consider Railway or Render.
