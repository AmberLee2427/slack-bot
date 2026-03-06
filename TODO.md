# Nancy Project TODO

## Slack
- [x] connect
- [x] test
  - Nancy says retrival and search are being wierd:
  > Amber  
  > [6:38 PM] I think I fixed your payload. You should have summaries now. And it should hopefully stop cutting you off
  > 18 repliesNancy  
  >  [6:38 PM] Searching knowledge base...
  >  [6:38 PM] Retrieving file: microlens_submit/microlens-submit/README.md
  >  [6:38 PM] Searching for: MulensModel FSPL parameters limit 3]
  >  [6:38 PM] Exploring knowledge base structure
  >  [6:38 PM]Yes, I can hear you loud and clear!  
  >
  >  I can see the document summaries are now included in my search results, which is excellent. The payload looks much better structured.
  >
  >  Let me test a few things to make sure everything is working properly...
  >  [6:38 PM] Searching for: select id, text from txtai where text like '%FSPL%' and text like '%MulensModel%' limit 5][6:38 PM] Exploring knowledge base structure[6:38 PM]I'm encountering some issues with the tools:
  > 
  >   1. TREE command: The root directory search failed. I'm trying to explore specific subdirectories instead.
  >
  >   2. RETRIEVE command: The file path microlens_submit/microlens-submit/README.md wasn't found in the index. This could mean:
  >    - The path structure is different than expected
  >    - The file hasn't been indexed
  >    - There's a path formatting issue
  >
  >   3. SEARCH results: The results for "MulensModel FSPL parameters" seem off-topic - I'm getting zodiacal light README files and benchmark test descriptions instead of actual MulensModel FSPL parameter documentation.
  >
  >  Let me try to get a better understanding of the directory structure and search capabilities...
  >  [6:38 PM] Searching for: FSPL model MulensModel point source point lens limit 10][6:38 PM] Searching for: README documentation microlensing limit 10][6:38 PM] Searching for: file directory structure limit 5][6:38 PM]I'm seeing several systematic issues:
  > 
  >  Tool Problems:
  >   1. TREE command: All directory lookups are failing (root, microlens_submit, microlensing_tools). This suggests either:
  >    - The directory tree isn't indexed
  >    - The TREE tool needs a different path format
  >    - The knowledge base structure is different than expected
  >
  >   2. SQL Search: The SQL query syntax failed - it seems the system may not support SQL queries or needs different syntax
  >
  >   3. File paths: The RETRIEVE command consistently fails, suggesting path resolution issues
  >
  >  Let me try some broader natural language searches to understand what's actually in the knowledge base...
  >  [6:38 PM] Retrieving file: microlensing_tools/MulensModel/examples/run_time_tests/README.md
  >  [6:38 PM] Retrieving file: web_resources/microlensing-online/README.md
  >  [6:38 PM] Searching for: tutorials examples MulensModel limit 10]
  >  [6:38 PM] Searching for: installation setup getting started limit 10]
  >  [6:38 PM]I'm noticing a pattern in the issues:
  >
  >  Search Results Pattern:
  >  Every search query is returning the same small set of files:
  >   - microlensing_tools/MulensModel/examples/run_time_tests/README.md (always top result)
  >   - microlens_submit/microlens-submit/tests/example_note.md (markdown test file)
  >   - Various WFI technical README files
  >   - web_resources/microlensing-online/README.md
  >
  >  This suggests the search might not be working correctly, or the knowledge base might be very limited.
  > 
  >  Let me try retrieving files that ARE appearing in the search results to test if RETRIEVE works at all...
  >  [6:39 PM]Major Issues Identified:
  > 
  >   1. RETRIEVE Tool - Complete Failure
  >    - ALL file retrieval attempts fail, even for files that appear in search results
  >    - Files tested:
  >    - microlens_submit/microlens-submit/README.md 
  >    - microlensing_tools/MulensModel/examples/run_time_tests/README.md 
  >    - web_resources/microlensing-online/README.md 
  >    - This suggests the retrieval index is either empty, corrupted, or using a different path format than the search index
  > 
  >   2. TREE Tool - Complete Failure
  >    - All directory lookups fail (root directory '', microlens_submit, microlensing_tools)
  >    - This suggests the directory tree structure is not indexed or the TREE tool isn't connected properly
  >
  >   3. SEARCH Tool - Limited/Repetitive Results
  >    - Every query returns the same ~5 files regardless of search terms
  >    - The files appear to be indexed (they show up in search), but:
  >    - Search ranking seems broken (same files, same order every time)
  >    - No variation in results despite different queries
  >    - The "Content length" metadata suggests the search index only has snippets, not full content
  >
  >   4. SQL Search - Not Functioning
  >    - SQL-style queries fail completely
  >
  >  Technical Hypothesis:
  >  Based on these symptoms, it appears:
  >   - The search index exists and has metadata about files (paths, snippets)
  >   - The retrieval system either doesn't have the actual file content, or there's a path mismatch between indexing and retrieval
  >   - The directory tree structure isn't indexed for the TREE tool
  >
  >  What's Working:
  >  You can see my responses
  >  The search returns something (even if limited)
  >  File metadata (paths, scores) are being transmitted
  > 
  >  What Needs Fixing:
  >   1. Connection between search index paths and retrieval system paths
  >   2. Population of the retrieval index with actual file content
  >   3. Directory tree indexing for TREE tool
  >   4. Search result diversity (currently returning same files for every query)

  ^ We only got as far as adding more dicument summaries, but the number of indexed files is still low in the UI. The summaries take so long that the builds haven't been finishing recently. It may pay to do a KB build skipping summaries and see which of these issues remain, and if the number of indexed files goes up on the UI.


  > Amber  
  > [5:03 PM] are you up and working, nancy?
  > 2 replies
  >  Nancy  
  >  [5:03 PM] Searching knowledge base...
  >  [5:04 PM] Yes! I'm up and working! 
  >
  >  I can see you've been making improvements to my RAG system - it looks like you've added document summaries and fixed some payload issues. That's great!
  > 
  >  However, I notice that while my RAG system reports as available, I'm not actually receiving any search results for this query. This could be because:
  >   • This is a simple greeting/status check that doesn't require knowledge base retrieval
  >   • The search functionality might need a test with a more technical query
  > 
  >  Would you like to test my knowledge base access with a microlensing-specific question? That would help verify that the document summaries and improved retrieval are working as expected.
  > 
  >  How can I help you with the Roman microlensing data challenge today?
- [ ] debug

## Hosting
- [x] permanent hosting with Nancy Brain
        * [x] trialed on mac
        * [x] implemented on Intel NUC
- stdio connection between Nancy Brain and Nancy Bot? 
    - I can't remember what I ended up getting the docker to do. I think it was basically this.
- https <- the "s"
- cloudflare
    - made a tunnel for nancy on the mac intending to migrate to lenovo, using the CLI
    - migrated to the InetlNUC instead
    - Dylan wants me to use the audiobook tunnel already forwarding to the lenovo and set it up on the website; CBF
    - can I host the nancy-brain UI without it being a security problem? Dunno, but I am.
- Docker
    - [x] Slack Bot Docker Setup (root directory)
        * [x] Dockerfile for the bot service
        * [x] docker-compose.yml connecting bot → MCP server
        * [x] Environment variable management
    - [x] API Key Configuration
        * [x] Add MCP_API_KEY to both services
        * [x] Update MCPRAGAdapter to send auth headers
    - [x] Update GitHub secrets
- integrate other MCP servers into the client
    - v3 of the slackbot might need to be an actual MCP client

## Aesthetics
- rename repo as `nancy-bot` (AKA Nancy Bot)

## Nancy-Brain
- [ ] ADS library integration
- more MCP tools (docker mcp wrapper them(?) and repackage selected useful tools as internal)
- Docker
    - [x] MCP Server Dockerization (in ref/nancy-brain/)
        * [x] Create Dockerfile with embeddings build step
        * [x] Add /rebuild API endpoint for triggering updates
        * [x] Implement simple API key auth middleware
        * check on the knowledgebase build
- live knowledge base udpates through tool calls

## v0.5.0 Focus
- [ ] App Home: inject live MCP/RAG health block
- [ ] Periodic MCP health polling + status refresh
- [ ] Validate NancyGPT + Actions against hosted MCP
- [ ] Resolve retrieve/tree/search reliability edge cases
