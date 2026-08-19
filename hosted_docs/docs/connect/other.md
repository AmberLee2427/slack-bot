# Other MCP clients

Use these connection values in any client that supports Streamable HTTP and
custom headers:

| Setting | Value |
| --- | --- |
| Transport | Streamable HTTP |
| MCP URL | `https://mcp.rges-pit.com/mcp` |
| Header name | `X-API-Key` |
| Header value | Your personal Nancy API key |

Nancy also accepts:

```text
Authorization: Bearer YOUR_PERSONAL_KEY
```

## Minimal protocol check

A plain browser request to `/mcp` is not a valid MCP request. It should return
`401` without a key. Use an MCP client or the official MCP Inspector for a full
protocol test. Modern MCP 2 clients use sessionless requests; older clients are
also supported through their legacy initialized session.

The unauthenticated health endpoint is:

```bash
curl https://mcp.rges-pit.com/health
```
