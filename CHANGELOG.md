# Changelog

## [Unreleased]
- Next target: `v0.5.0` implementation and beta hardening.
- Planned focus:
  - Slack home RAG health surface + periodic MCP re-check.
  - MCP reliability fixes for retrieve/tree/search edge cases.
  - NancyGPT + Actions integration validation.
  - Deployment readiness for hosted MCP usage.

## [0.4.1] - 2026-02-04
- Documentation cleanup for release-state clarity.
- Marked `v0.4.x` containerization baseline as complete and moved active work to `v0.5.x`.
- Clarified MCP-only architecture and test expectations in project docs.

## [0.4.0] - 2025-08-28
- MCPRAGAdapter integrated as sole RAG backend; legacy RAGService removed.
- Bot and MCP server refactored for chunked/passage retrieval compatibility.
- Unit and integration test infrastructure updated:
  - Pytest fixture starts/stops MCP server for integration tests.
  - Tests for passage retrieval, context assembly, and Slack command handling.
- README.md and AGENTS.md updated for new architecture, test setup, and usage.
- Manual QA checklist added (MANUAL_QA.md).
- Rate limiting and health/status UI improved.
- Documentation clarified for MCP_API_KEY usage and test environment setup.
