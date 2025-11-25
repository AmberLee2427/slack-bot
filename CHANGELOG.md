# Changelog

## [Unreleased]
- Initial creation of changelog.

## [2025-11-23]
- MCPRAGAdapter integrated as sole RAG backend; legacy RAGService removed.
- Bot and MCP server refactored for chunked/passage retrieval compatibility.
- Unit and integration test infrastructure updated:
  - Pytest fixture starts/stops MCP server for integration tests.
  - Tests for passage retrieval, context assembly, and Slack command handling.
- README.md and AGENTS.md updated for new architecture, test setup, and usage.
- Manual QA checklist added (MANUAL_QA.md).
- Rate limiting and health/status UI improved.
- Documentation clarified for MCP_API_KEY usage and test environment setup.

## [Earlier]
- Slack bot initial implementation and configuration.
- Knowledge base pipeline moved to nancy-brain MCP server.
- Basic retrieval, search, and Slack integration features.
