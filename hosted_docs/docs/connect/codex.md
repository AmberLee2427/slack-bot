# Codex

Codex can connect directly to Nancy using a bearer token. Nancy accepts the
same personal key through either `Authorization: Bearer` or `X-API-Key`.

## Add the server

Store the key in your shell environment:

```bash
export NANCY_MCP_API_KEY="YOUR_PERSONAL_KEY"
```

Then register Nancy:

```bash
codex mcp add nancy-microlensing \
  --url https://mcp.rges-pit.com/mcp \
  --bearer-token-env-var NANCY_MCP_API_KEY
```

Restart Codex if it is already open.

## Verify

```bash
codex mcp list
```

Then ask Codex:

> Search Nancy for finite-source point-lens parallax fitting examples.

!!! warning "Environment persistence"
    Shell exports last only for that shell session. Put the variable in your
    preferred secrets manager or shell startup configuration if you want it
    available after a reboot. Never commit the key.

