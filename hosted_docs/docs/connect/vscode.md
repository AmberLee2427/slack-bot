# VS Code

VS Code can connect directly to Nancy over Streamable HTTP.

## Add the server

Run **MCP: Open User Configuration** from the Command Palette and add:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "nancy-api-key",
      "description": "Nancy API key",
      "password": true
    }
  ],
  "servers": {
    "nancy-microlensing": {
      "type": "http",
      "url": "https://mcp.rges-pit.com/mcp",
      "headers": {
        "X-API-Key": "${input:nancy-api-key}"
      }
    }
  }
}
```

Start `nancy-microlensing` from **MCP: List Servers**. VS Code prompts for the
key without storing it in the JSON file.

## Verify

Open Chat in agent mode and ask:

> Use Nancy to find tutorials about annual microlensing parallax.

The tool-call details should show a Nancy search followed by one or more
retrieval calls.

## Troubleshooting

- `401 Invalid or missing API key`: re-enter the personal API key.
- Server unavailable: check [service health](https://mcp.rges-pit.com/health).
- No Nancy tools: run **MCP: List Servers**, select the server, and inspect its
  output log.

