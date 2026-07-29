# Claude

## Claude Code

Claude Code supports remote HTTP MCP servers with custom headers. Set the key
in your environment:

```bash
export NANCY_MCP_API_KEY="YOUR_PERSONAL_KEY"
```

Add this user-scoped entry to Claude Code:

```bash
claude mcp add --scope user --transport http \
  nancy-microlensing https://mcp.rges-pit.com/mcp \
  --header "X-API-Key: \${NANCY_MCP_API_KEY}"
```

Inside Claude Code, run `/mcp` to verify the connection.

## Claude.ai and Claude Desktop

Claude's remote connector interface currently supports authless and OAuth
servers. Nancy currently uses personal API keys rather than a complete MCP
OAuth flow, so the hosted service cannot yet be added directly through
**Settings > Connectors**.

Do not put the API key in the connector URL. Use Claude Code, VS Code, Codex,
or another client that supports custom request headers until OAuth support is
available.

