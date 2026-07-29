# Tools

Nancy provides five primary MCP tools.

## Search

Semantic retrieval across indexed software, documentation, notebooks, and
papers. Start broad, inspect results, and retrieve the strongest sources.

## Retrieve

Read a source document or a bounded line range. Retrieved results include
stable document identifiers and provenance metadata.

## Tree

Explore indexed paths without requiring the original raw repository checkout.
Both short indexed paths and the historical `knowledge_base/raw/` prefix are
accepted.

## Weight

Apply a personal multiplier from `0.5` to `2.0` to influence subsequent search
ranking. Weighting is useful when a toolkit, tutorial, or paper is especially
authoritative for your work. Preferences are stored against a one-way hash of
your API key and do not change another user's ranking.

## Status

Inspect service health and index metadata. This is the first diagnostic when
search results appear stale or the tools stop responding.

## Good agent instructions

Tell your assistant to search before answering, retrieve the relevant passages,
and cite source paths. For example:

> Search Nancy for finite-source point-lens parallax fitting. Retrieve the most
> relevant tutorial and implementation passages, then answer with source paths.
