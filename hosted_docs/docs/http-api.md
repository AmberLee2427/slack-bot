# HTTP API

The same service exposes a small HTTP API for scripts and diagnostics.

```bash
export NANCY_MCP_API_KEY="YOUR_PERSONAL_KEY"
```

## Search

```bash
curl -G https://mcp.rges-pit.com/search \
  -H "X-API-Key: ${NANCY_MCP_API_KEY}" \
  --data-urlencode "query=annual microlensing parallax" \
  --data-urlencode "limit=5"
```

## Retrieve

```bash
curl -X POST https://mcp.rges-pit.com/retrieve \
  -H "X-API-Key: ${NANCY_MCP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"doc_id":"DOCUMENT_ID","start":1,"end":80}'
```

## Tree

```bash
curl -G https://mcp.rges-pit.com/tree \
  -H "X-API-Key: ${NANCY_MCP_API_KEY}" \
  --data-urlencode "prefix=microlensing_tools" \
  --data-urlencode "depth=3"
```

## Health

```bash
curl https://mcp.rges-pit.com/health
```

The health endpoint is public. Search, retrieval, tree, weighting, SQL, and
rebuild operations require authentication.

