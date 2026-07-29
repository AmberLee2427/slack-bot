<section class="nb-hero">
  <div class="nb-hero__copy">
    <p class="nb-eyebrow">RGES-PIT · Shared research infrastructure</p>
    <h1><span>Microlensing context,</span><span>on demand.</span></h1>
    <p class="nb-lede">
      Nancy is a searchable knowledge base for microlensing software,
      documentation, tutorials, notebooks, and literature. Connect it to an
      MCP-capable assistant and ask questions where you already work.
    </p>
    <div class="nb-actions">
      <a class="md-button md-button--primary" href="connect/vscode/">Connect from VS Code</a>
      <a class="md-button" href="connect/codex/">Connect from Codex</a>
    </div>
  </div>
  <div class="nb-hero__mark" aria-hidden="true">
    <img src="assets/nancy-brain2.png" alt="">
  </div>
</section>

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

<aside class="nb-origin">
  <img src="assets/nancy-portrait.png" alt="Illustrated portrait of Nancy Grace Roman">
  <div>
    <p class="nb-eyebrow">Why Nancy?</p>
    <h2>Built for the Roman microlensing community.</h2>
    <p>
      Nancy is named for astronomer Nancy Grace Roman. The service keeps
      microlensing references close at hand while leaving interpretation and
      scientific judgment with the researcher.
    </p>
  </div>
</aside>

## Building your own knowledge base

This site documents the shared microlensing service. To build, configure, or
self-host a different knowledge base, use the
[Nancy Brain package documentation](https://nancy-docs.malpas.nz/).
