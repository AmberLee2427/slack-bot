# Nancy Project TODO

## Slack
- connect
- test
- debug

## Hosting
- [ ] permanent hosting with Nancy Brain
        * [x] trialed on mac
        * [ ] implemented on lenovo
- stdio connection between Nancy Brain and Nancy Bot? 
    - probably not; CBF.
- https <- the "s"
- cloudflare
    - made a tunnel for nancy on the mac intending to migrate to lenovo, using the CLI
    - Dylan wants me to use the audiobook tunnel already forwarding to the lenovo and set it up on the website
    - can I host the nancy-brain UI without it being a security problem?
- Docker
    - [ ] Slack Bot Docker Setup (root directory)
        * [x] Dockerfile for the bot service
        * [x] docker-compose.yml connecting bot → MCP server
        * [x] Environment variable management
    - [ ] API Key Configuration
        * [x] Add MCP_API_KEY to both services
        * [x] Update MCPRAGAdapter to send auth headers
    - [ ] Update GitHub secrets
- integrate other MCP servers into the client
    - v3 of the slackbot might need to be an actual MCP client

## Aesthetics
- rename repo as `nancy-bot` (AKA Nancy Bot)

## Nancy-Brain
- ADS library integration
- more MCP tools (docker them(?) and repackage selected useful tools as internal)
- Docker
    - [x] MCP Server Dockerization (in ref/nancy-brain/)
        * [x] Create Dockerfile with embeddings build step
        * [x] Add /rebuild API endpoint for triggering updates
        * [x] Implement simple API key auth middleware
        * check on the knowledgebase build
- live knowledge base udpates through tool calls