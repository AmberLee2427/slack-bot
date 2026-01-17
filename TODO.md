# Nancy Project TODO

## Slack
- connect
- test
- debug

## Hosting
- permanent hosting with Nancy Brain
- stdio connection between Nancy Brain and Nancy Bot
- Docker
    - [ ] Slack Bot Docker Setup (root directory)
        * [ ] Dockerfile for the bot service
        * [ ] docker-compose.yml connecting bot → MCP server
        * [ ] Environment variable management
    - [ ] API Key Configuration
        * [ ] Add MCP_API_KEY to both services
        * [ ] Update MCPRAGAdapter to send auth headers
- integrate other MCP servers into the client

## Aesthetics
- rename repo as `nancy-bot` (AKA Nancy Bot)

## Nancy-Brain
- ADS library integration
- more MCP tools (docker them(?) and repackage selected useful tools as internal)
- Docker
    - [ ] MCP Server Dockerization (in ref/nancy-brain/)
        * [ ] Create Dockerfile with embeddings build step
        * [ ] Add /rebuild API endpoint for triggering updates
        * [ ] Implement simple API key auth middleware
- live knowledge base udpates through tool calls