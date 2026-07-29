# Microlensing context, on demand

Nancy is a shared, searchable knowledge base for microlensing software,
documentation, tutorials, notebooks, and literature. Connect it to an
MCP-capable assistant and ask questions in the environment where you already
work.

[:material-connection: Connect from VS Code](connect/vscode.md){ .md-button .md-button--primary }
[:material-console: Connect from Codex](connect/codex.md){ .md-button }

## What you need

1. An invite code from the Nancy administrators.
2. A personal Nancy API key.
3. An MCP client that supports Streamable HTTP and custom authentication
   headers.

Request your personal key once:

```bash
curl -X POST https://mcp.rges-pit.com/v2/api-keys/request \
  -H "Content-Type: application/json" \
  -d '{"invite_code":"YOUR_INVITE_CODE","contact":"you@example.com"}'
```

The response contains `api_key`. Store it as a password: do not commit it to a
repository, paste it into a shared configuration file, or post it in Slack.

!!! info "Already using the old address?"
    `https://nancy-brain.malpas.nz` remains supported. The RGES-PIT address is
    an additional stable name for the same service.

## What Nancy can do

- Search the microlensing knowledge base semantically.
- Retrieve precise passages with source and line metadata.
- Explore indexed document and repository trees.
- Apply personal retrieval weights to prioritize useful sources.
- Report service and index status.

Nancy exposes knowledge-base tools, not a language model. Your chosen AI client
decides how to use the returned evidence and generates the answer.

## Building your own knowledge base

This site documents the shared microlensing service. To build, configure, or
self-host a different knowledge base, use the
[Nancy Brain package documentation](https://nancy-docs.malpas.nz/).

