# Nancy Bot Architecture

## Refactored Design

We've moved away from slack-machine to a simple, focused HTTP-based bot that matches your exact needs.

### Key Changes Made:

1. **Removed slack-machine dependency** - built lightweight HTTP bot instead
2. **Fixed naming consistency** - everything uses `LLMService` now  
3. **Separated concerns** - tools return data, bot handles Slack communication
4. **Async-friendly** - LLM processing runs in thread pool to avoid blocking

### Architecture:

```
nancy_bot.py                 # Main bot - handles HTTP events from Slack
├── bot/plugins/
│   ├── llm/
│   │   ├── llm_service.py   # LLMService - orchestrates multi-turn conversations
│   │   ├── tools.py         # Tools return data instead of sending to Slack
│   │   └── system_prompt.txt
│   └── rag/
│       └── rag_service.py   # RAGService - unchanged
```

### How it works:

1. **Slack sends events** → `nancy_bot.py` via HTTP
2. **Bot validates signature** and processes mentions/DMs  
3. **LLMService.call_llm()** handles multi-turn conversation:
   - Searches knowledge base
   - Retrieves files
   - Collects responses during turns
   - Returns final compiled response
4. **Bot sends response** to Slack

### Benefits:

- ✅ **No Socket Mode** - uses your manifest exactly
- ✅ **Minimal dependencies** - only what Nancy needs
- ✅ **Clean separation** - tools don't directly send to Slack
- ✅ **Multi-response handling** - collects responses from all turns
- ✅ **Easy to deploy** - simple HTTP server
- ✅ **Your RAG/LLM logic unchanged** - just cleaner interfaces

### Next Steps:

1. Install dependencies: `pip install -e .`
2. Copy `bot/config/.env.example` → `bot/config/.env` and fill in tokens
3. Run: `python nancy_bot.py`
4. Set your Slack app's event URL to your server + `/slack/events`

The core intelligence (RAG + LLM + tools) stays exactly the same - we just made the bot infrastructure simpler and more focused.
