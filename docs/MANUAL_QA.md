# Nancy Slack Bot Manual QA Checklist

## 1. Search Functionality
- **Action:** Ask Nancy a question that triggers a knowledge base search (e.g., "@nancy What is microlensing?").
- **Expected:** Nancy returns a list of relevant documents/passages, with scores and context snippets.
- **Check:** Results are relevant, scores are shown, context is clear.

## 2. Passage Retrieval
- **Action:** Request a specific passage (e.g., "@nancy show lines 10-30 of microlensing_tools/MulensModel/README.md").
- **Expected:** Nancy returns only the requested lines, with file name and line numbers.
- **Check:** Passage boundaries are correct, metadata is present, formatting is readable.

## 3. Whole File Retrieval
- **Action:** Request a whole file (e.g., "@nancy show microlensing_tools/MulensModel/README.md").
- **Expected:** Nancy returns the full file content, or paginates if too large.
- **Check:** No missing content, file name is shown, formatting is readable.

## 4. Slack Bot UI
- **Action:** Open Nancy’s Slack home view and use the /status command.
- **Expected:** Health/status block shows MCP status, last-checked time, and subsystem health.
- **Check:** Status is accurate, UI is clear, error states are handled gracefully.

## 5. Rate Limiting
- **Action:** Send multiple queries to Nancy until the daily limit is reached.
- **Expected:** Nancy warns as you approach the limit, and blocks further queries when exceeded.
- **Check:** Messages are clear, limits reset at midnight UTC.

## 6. Error Handling
- **Action:** Simulate MCP server downtime (stop the server, then query Nancy).
- **Expected:** Nancy reports MCP is unavailable, fails gracefully, and logs the error.
- **Check:** No crashes, error messages are user-friendly.

## 7. Documentation
- **Action:** Review README.md and AGENTS.md for setup, usage, and troubleshooting instructions.
- **Expected:** Docs are up to date, clear, and cover all major features and changes.

---

# Notes
- Record any bugs, unclear responses, or missing features.
- If you find a bug, note the exact query, expected vs. actual result, and any error messages.
- Update the changelog with any fixes or new features found during manual QA.
