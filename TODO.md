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
        * [x] Dockerfile for the bot service
        * [x] docker-compose.yml connecting bot → MCP server
        * [x] Environment variable management
    - [ ] API Key Configuration
        * [x] Add MCP_API_KEY to both services
        * [x] Update MCPRAGAdapter to send auth headers
- integrate other MCP servers into the client

## Aesthetics
- rename repo as `nancy-bot` (AKA Nancy Bot)

## Nancy-Brain
- ADS library integration
- more MCP tools (docker them(?) and repackage selected useful tools as internal)
- Docker
    - [ ] MCP Server Dockerization (in ref/nancy-brain/)
        * [x] Create Dockerfile with embeddings build step
        * [x] Add /rebuild API endpoint for triggering updates
        * [x] Implement simple API key auth middleware
- live knowledge base udpates through tool calls