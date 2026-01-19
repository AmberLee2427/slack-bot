"""
This module contains the LLM service for Nancy using Claude (Anthropic).
"""

import os
from pathlib import Path
import yaml
import json
import re
import difflib
import requests
from dotenv import load_dotenv
from anthropic import Anthropic

# environment file 
env_path = Path("bot/config/.env")
load_dotenv(env_path)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
DEBUG_LLM = os.environ.get("DEBUG_LLM", "False").lower() in ("true", "1", "yes")
DAILY_RATE_LIMIT = int(os.environ.get("DAILY_RATE_LIMIT", "100"))  # Default 100 queries per user per day

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

class LLMService:
    def __init__(
            self, 
            system_prompt: Path = None, 
            max_turns: int = 5, 
            model_weights_path: Path = None,
            debugging: bool = None,  # Use None to read from env
            no_of_retrievals: int = 5,
            rag_service=None,  # Accept existing RAG service
            daily_rate_limit: int = None  # Daily queries per user (None = use env var)
        ):
        # Use Nancy's base directory for all paths
        nancy_base = Path(os.environ.get("NANCY_BASE_DIR", "."))
        
        # Set default paths relative to Nancy's base
        if system_prompt is None:
            system_prompt = nancy_base / "bot/plugins/llm/system_prompt.txt"
        if model_weights_path is None:
            model_weights_path = nancy_base / "config" / "model_weights.yaml"
        
        # Set rate limit from environment if not specified
        if daily_rate_limit is None:
            daily_rate_limit = DAILY_RATE_LIMIT
        
        # Set debugging from environment if not specified
        if debugging is None:
            debugging = DEBUG_LLM
            
        # persisting variables
        self.system_prompt_path = system_prompt
        self.max_turns = max_turns
        self.model_weights_path = model_weights_path
        self.debugging = debugging
        self.no_of_retrievals = no_of_retrievals
        self.update_weights()
        
        # Load system prompt content
        with open(self.system_prompt_path, 'r') as f:
            self.system_prompt = f.read()

        # Initialize rate limiter
        from bot.utils.rate_limiter import DailyRateLimiter
        self.rate_limiter = DailyRateLimiter(daily_limit=daily_rate_limit)

        # Log debugging state
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"LLM Service initialized with debugging={'ON' if self.debugging else 'OFF'}")
        logger.info(f"Daily rate limit set to: {daily_rate_limit} queries per user")

        # RAG backend: require MCPRAGAdapter, fail fast if not configured
        MCP_BASE_URL = os.environ.get("MCP_BASE_URL")
        MCP_API_KEY = os.environ.get("MCP_API_KEY")
        if not MCP_BASE_URL:
            logger.error("MCP_BASE_URL is not set. MCPRAGAdapter is now required as the only supported RAG backend. Exiting.")
            raise RuntimeError("MCP_BASE_URL is required for Nancy. No legacy RAGService fallback is available.")
        from bot.plugins.rag.mcp_adapter import MCPRAGAdapter
        try:
            self.rag = MCPRAGAdapter(MCP_BASE_URL, api_key=MCP_API_KEY)
            # Health check
            health_url = MCP_BASE_URL.rstrip('/') + '/health'
            health_headers = {}
            if MCP_API_KEY:
                health_headers['X-API-Key'] = MCP_API_KEY
            resp = requests.get(health_url, headers=health_headers, timeout=5)
            if not resp.ok:
                logger.error("MCP RAG health check failed: %s: %s", resp.status_code, resp.text)
                raise RuntimeError(f"MCPRAGAdapter health check failed: {resp.status_code} {resp.text}")
            self.rag_status = {"available": True, "source": "mcp"}
            logger.info("Using MCPRAGAdapter pointing to %s (health OK)", MCP_BASE_URL)
        except Exception as e:
            logger.error("Failed to initialize MCPRAGAdapter or health-check (%s): %s", MCP_BASE_URL, e)
            raise RuntimeError(f"Failed to initialize MCPRAGAdapter: {e}")
        # Build a list of all indexed file paths from the embeddings database (once)
        # If RAG is unavailable we still allow the bot to run; update_rag_variables
        # will handle the None case.
        self.update_rag_variables()

        # Thread context caching - tracks what files Nancy has looked at per thread
        # Format: {thread_ts: (timestamp, [doc_id1, doc_id2, doc_id3])}
        self.thread_cache_path = nancy_base / "bot/config/thread_cache.json"
        self.thread_retrievals = self._load_thread_cache()

        # import tools
        from bot.plugins.llm.tools import (
            retrieve_tool, 
            weight_tool, 
            response_tool, 
            search_tool, 
            tree_tool
        )
        self.retrieve_tool = retrieve_tool
        self.weight_tool = weight_tool
        self.response_tool = response_tool
        self.search_tool = search_tool
        self.tree_tool = tree_tool
    
    def _load_thread_cache(self):
        """Load thread cache from disk"""
        try:
            if self.thread_cache_path.exists():
                with open(self.thread_cache_path, 'r') as f:
                    data = json.load(f)
                    # Convert string keys back to proper format
                    thread_cache = {}
                    for thread_ts, (timestamp, files) in data.items():
                        thread_cache[thread_ts] = (timestamp, files)
                    
                    if self.debugging:
                        logger = __import__('logging').getLogger(__name__)
                        logger.info(f"Loaded thread cache with {len(thread_cache)} threads")
                    return thread_cache
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.warning(f"Failed to load thread cache: {e}")
        
        return {}
    
    def _save_thread_cache(self):
        """Save thread cache to disk"""
        try:
            # Ensure directory exists
            self.thread_cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.thread_cache_path, 'w') as f:
                json.dump(self.thread_retrievals, f, indent=2)
                
            if self.debugging:
                logger = __import__('logging').getLogger(__name__)
                logger.info(f"Saved thread cache with {len(self.thread_retrievals)} threads")
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"Failed to save thread cache: {e}")

    def _prune_thread_cache(self, max_threads: int = 50):
        """Prune thread cache to keep only the most recent threads"""
        if len(self.thread_retrievals) > max_threads:
            # Sort by timestamp (newest first) and keep only the most recent
            sorted_threads = sorted(
                self.thread_retrievals.items(), 
                key=lambda x: x[1][0], 
                reverse=True
            )
            
            # Keep only the top max_threads
            self.thread_retrievals = dict(sorted_threads[:max_threads])
            
            if self.debugging:
                logger = __import__('logging').getLogger(__name__)
                logger.info(f"Pruned thread cache to {len(self.thread_retrievals)} threads")
            
            # Save after pruning
            self._save_thread_cache()

    def update_rag_variables(self):
        # If RAG is not available, populate empty structures and return
        if not getattr(self, 'rag', None):
            self.all_indexed_files = []
            self.indexed_file_map = {}
            return

        # Best-effort warmup: MCP can be slow on first boot while loading embeddings.
        # Nancy should still start and respond in Slack even if this query times out.
        try:
            all_indexed_docs = list(self.rag.embeddings.database.search("select id, text from txtai"))
            self.all_indexed_files = [doc['id'] for doc in all_indexed_docs if doc.get('id')]
            self.indexed_file_map = {doc['id']: doc.get('text', '') for doc in all_indexed_docs if doc.get('id')}
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.warning(f"RAG warmup (embeddings SQL) failed; continuing without file index: {e}")
            self.all_indexed_files = []
            self.indexed_file_map = {}
    
    def update_weights(self):
        if self.model_weights_path.exists():
            with open(self.model_weights_path, "r") as f:
                self.model_weights = yaml.safe_load(f) or {}
        else:
            self.model_weights = {}

    def get_initial_context(self, query: str, thread_ts: str = None) -> str:
        """Get initial context - either from thread cache or RAG search"""
        import time
        
        # If we're in a thread and have cached context, use that instead of RAG
        if thread_ts and thread_ts in self.thread_retrievals:
            timestamp, cached_doc_ids = self.thread_retrievals[thread_ts]
            if cached_doc_ids:
                logger = __import__('logging').getLogger(__name__)
                logger.info(f"Using cached thread context: {len(cached_doc_ids)} files from thread {thread_ts}")
                
                # Get content from cached files
                context_parts = []
                for doc_id in cached_doc_ids:
                    if doc_id in self.indexed_file_map:
                        github_url = None
                        if getattr(self, 'rag', None):
                            try:
                                github_url = self.rag._get_github_url(doc_id)
                            except Exception:
                                github_url = None
                        if github_url:
                            # Provide both file path (for tools) and GitHub URL (for users)
                            context_parts.append(f"Source: {doc_id}\nGitHub URL: {github_url}\n{self.indexed_file_map[doc_id]}")
                        else:
                            context_parts.append(f"Source: {doc_id}\n{self.indexed_file_map[doc_id]}")
                
                if context_parts:
                    return "\n\n".join(context_parts)
                # Fallback to RAG only if available
                if getattr(self, 'rag', None):
                    return self.rag.get_context_for_query(query)
                # Otherwise return a placeholder noting RAG is unavailable
                return f"[RAG UNAVAILABLE: {self.rag_status}]\nNo knowledge-base context available."
        
        # Normal RAG search for channel messages or new threads
        if getattr(self, 'rag', None):
            try:
                return self.rag.get_context_for_query(query)
            except Exception:
                return f"[RAG UNAVAILABLE: {self.rag_status}]\nNo knowledge-base context available."
        else:
            return f"[RAG UNAVAILABLE: {self.rag_status}]\nNo knowledge-base context available."

    def construct_query_payload(self, query: str, context: str, conversation_history: list = None) -> dict:
        """
        Construct a payload for Claude API.
        Returns a dict with 'system' prompt and 'messages' list.
        """
        # Add conversation history if available
        messages = []
        if conversation_history:
            for msg in conversation_history:
                user_id = msg.get("user", "Unknown")
                text = msg.get("text", "")
                is_bot = msg.get("is_bot", False)
                
                if is_bot:
                    # This is Nancy's previous response
                    messages.append({"role": "assistant", "content": text})
                else:
                    # This is a user message
                    if user_id.startswith("U"):
                        messages.append({"role": "user", "content": f"<@{user_id}>: {text}"})
                    else:
                        messages.append({"role": "user", "content": f"{user_id}: {text}"})
        
        # Current user query with context
        user_message = (
            f"You will have {self.max_turns} internal turns to answer the user's question.\n"
            f"\n"
            f"User query:\n"
            f"{query}\n"
            f"\n"
            f"Relevant search results:\n"
            f"{context}\n"
        )
        messages.append({"role": "user", "content": user_message})

        return {
            "system": self.system_prompt,
            "messages": messages
        }

    def querry_llm(self, payload: dict, turn: int, user_id: str = None) -> tuple[str, str]:
        import logging
        logger = logging.getLogger(__name__)
        
        # Rate limiting check (only on first turn to avoid multiple charges per conversation)
        if turn == 0 and user_id:
            allowed, used_today, remaining = self.rate_limiter.check_and_increment(user_id)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for user {user_id}: {used_today} queries used today")
                # Return a rate limit message instead of calling the API
                rate_limit_msg = (
                    f"🚫 *Daily Limit Reached*\n\n"
                    f"You've used your {used_today} daily Nancy interactions. "
                    f"Your quota resets at midnight UTC.\n\n"
                    f"Need more access? Contact your administrator or try again tomorrow!"
                )
                return rate_limit_msg, f"\n\nTURN {turn+1}:\n\n{rate_limit_msg}\n"
            
            # Log successful rate limit check
            if remaining == 0:  # This was the last allowed query
                logger.warning(f"🟡 User {user_id} has reached their daily limit: {used_today}/{used_today + remaining}")
            elif remaining <= 10:  # Warning when getting low
                logger.info(f"⚠️ User {user_id} has {remaining} queries remaining today")
            else:
                logger.info(f"✅ User {user_id} rate limit check passed: {used_today}/{used_today + remaining} used")
        
        try:
            logger.info(f"Making Claude API request for turn {turn}")
            if self.debugging:
                logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
            
            # Call Claude API using Anthropic SDK
            response = anthropic_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=payload["system"],
                messages=payload["messages"]
            )

            # Save payload to file for debugging
            if self.debugging:
                os.makedirs("tests", exist_ok=True)
                with open(f"tests/payload_{turn}.json", "w") as f:
                    json.dump(payload, f)

            # Extract text from Claude response
            if response.content and len(response.content) > 0:
                llm_text = response.content[0].text
                if self.debugging:
                    logger.info(f"Full Claude response: {response}")
                    logger.info(f"LLM response text: {llm_text}")
                logger.info(f"Claude API response received for turn {turn}")
                assistant_response = f"\n\nTURN {turn+1}:\n\n"
                assistant_response += llm_text + "\n"
                return llm_text, assistant_response
            else:
                logger.error(f"Empty response from Claude API")
                return None, None
                
        except Exception as e:
            logger.error(f"Exception in querry_llm: {e}")
            return None, None

    def continue_with_extended_turns(self, callback_fn, conversation_history: list = None, thread_ts: str = None, additional_turns: int = 5, user_id: str = None):
        """
        Continue an existing conversation with extended turns (for "Keep Cooking" feature).
        
        Args:
            callback_fn: Function to call with intermediate updates
            conversation_history: Previous conversation context
            thread_ts: Thread timestamp for context
            additional_turns: How many additional turns to allow (default 5)
            user_id: Slack user ID for rate limiting
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🍳 Keep Cooking: Extending analysis with {additional_turns} additional turns")
        
        # Temporarily increase max turns for this session
        original_max_turns = self.max_turns
        self.max_turns = original_max_turns + additional_turns
        
        try:
            # Create a continuation prompt
            continuation_query = "Please continue your analysis and provide additional insights, examples, or deeper explanation on this topic."
            
            # Use the regular callback method but with extended turns
            result = self.call_llm_with_callback(
                query=continuation_query,
                callback_fn=callback_fn,
                conversation_history=conversation_history,
                thread_ts=thread_ts,
                user_id=user_id
            )
            
            return result
            
        finally:
            # Restore original max turns
            self.max_turns = original_max_turns

    def call_llm_with_callback(self, query: str, callback_fn, conversation_history: list = None, thread_ts: str = None, user_id: str = None):
        """
        Process a query with a callback function for sending intermediate updates.
        callback_fn(message: str, is_final: bool = False)
        conversation_history: list of recent messages for context
        thread_ts: Slack thread timestamp for context caching
        user_id: Slack user ID for rate limiting
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Log conversation history if provided
        if conversation_history:
            logger.info(f"Using conversation history with {len(conversation_history)} messages")
            if self.debugging:
                for i, msg in enumerate(conversation_history):
                    user = msg.get('user', 'Unknown')
                    text = msg.get('text', '')[:100]
                    is_bot = msg.get('is_bot', False)
                    logger.info(f"  Message {i+1}: {'[BOT] ' if is_bot else ''}#{user}: {text}...")
        else:
            logger.info("No conversation history provided")
        
        # Initialize the turn variables
        payload = None
        turn = 0
        searching = True
        context_files = set()
        meta_prompt = ""
        
        # Remove initial status message - too verbose
        # callback_fn("  :mag: _Searching for relevant information in knowledge base_", False)  # REMOVED

        # Get the initial context (from thread cache or RAG)
        logger.info("Getting initial context")
        context = self.get_initial_context(query, thread_ts)
        logger.info(f"Context length: {len(context)}")

        # Construct the initial payload
        logger.info("Constructing query payload")
        payload = self.construct_query_payload(query, context, conversation_history)

        # Loop through the turns
        while searching and turn < self.max_turns:
            logger.info(f"Starting LLM turn {turn}")

            # --- QUERY LLM ---
            llm_text, assistant_response = self.querry_llm(payload, turn, user_id)

            if llm_text is None:
                logger.error("LLM returned None - stopping")
                searching = False  # exit the loop
                # Provide a generic error message since the backend could be Claude or Gemini
                callback_fn("  :x: _Failed to connect to LLM Service_", True, hit_turn_limit=False)
                return
            
            # Check if this is a rate limit response
            if "🚫 *Daily Limit Reached*" in llm_text:
                logger.info("Rate limit response detected - stopping processing")
                callback_fn(llm_text, True, hit_turn_limit=False)  # Send rate limit message as final response
                return
            # --- END QUERY LLM ---

            # Begin new turn in the meta prompt
            meta_prompt += f"\n\nTURN {turn+1} REQUESTS:\n\n"
            
            # Log what tools are detected (debugging mode)
            if self.debugging:
                logger.info(f"Tool detection - RETRIEVE: {'RETRIEVE:' in llm_text}")
                logger.info(f"Tool detection - WEIGHT: {'WEIGHT:' in llm_text}")
                logger.info(f"Tool detection - SEARCH: {'SEARCH:' in llm_text}")
                logger.info(f"Tool detection - TREE: {'TREE:' in llm_text}")
                logger.info(f"Tool detection - RESPONSE: {'RESPONSE' in llm_text}")

            # --- RETRIEVE tool handler ---
            file_paths = []
            if "RETRIEVE:" in llm_text:
                # Support multiple RETRIEVE: lines
                lines = llm_text.splitlines()
                for line in lines:
                    if "RETRIEVE:" in line:
                        path = line.split("RETRIEVE:")[1].strip().split()[0].rstrip("]")
                        file_paths.append(path)

                # Loop through the requested file paths
                for file_path in file_paths:
                    # Get GitHub URL for display
                    github_url = self.rag._get_github_url(file_path)
                    if github_url:
                        filename = Path(file_path).name
                        display_link = f"<{github_url}|{filename}>"
                        callback_fn(f"  :page_facing_up: _Retrieving file:_ {display_link}", False)
                    else:
                        callback_fn(f"  :page_facing_up: _Retrieving file:_ `{file_path}`", False)
                    # Skip if file already in context
                    if file_path in context_files:
                        continue
                    else:
                        meta_prompt_addition, new_context_files = self.retrieve_tool(
                            self,
                            file_path, 
                            context_files
                        )  # Retrieves the file content for each file
                        context_files.update(new_context_files)
                        meta_prompt += meta_prompt_addition
            # --- END RETRIEVE tool handler ---

            # --- WEIGHT tool handler ---
            if "WEIGHT:" in llm_text:
                callback_fn("  :scales: _Adjusting knowledge base weights_", False)
                self.model_weights, meta_prompt_addition = self.weight_tool(
                    self,
                    llm_text, 
                    self.model_weights, 
                    self.model_weights_path
                )  # Performs weighting and updates the model weights
                meta_prompt += meta_prompt_addition
            # --- END WEIGHT tool handler ---

            # --- SEARCH tool handler ---
            if "SEARCH:" in llm_text:
                # Remove redundant "Performing targeted search" message
                # callback_fn("  :mag_right: _Performing targeted search_", False)  # REMOVED
                meta_prompt_addition = self.search_tool(
                    self,
                    llm_text, callback_fn
                )  # Perform a new search if the agent has requested it
                meta_prompt += meta_prompt_addition
            # --- END SEARCH tool handler ---

            # --- TREE tool handler ---
            if "TREE:" in llm_text:
                callback_fn("  :deciduous_tree: _Exploring knowledge base structure_", False)
                meta_prompt_addition = self.tree_tool(
                    self,
                    llm_text
                )  # Gets the requested file tree
                meta_prompt += meta_prompt_addition
            # --- END TREE tool handler ---

            # --- RESPONSE tool handler ---
            # Extract the comment from the LLM response and send it
            if self.debugging:
                logger.info(f"Checking for RESPONSE in LLM text. Full text: {llm_text}")
            if "RESPONSE" in llm_text:
                if self.debugging:
                    logger.info("Found RESPONSE in LLM text, extracting...")
                try:
                    response_text = self.response_tool(self, llm_text)
                    if self.debugging:
                        logger.info(f"Extracted response: {response_text}")
                    if response_text:
                        if self.debugging:
                            logger.info("Sending response to callback")
                        callback_fn(response_text, True, hit_turn_limit=False)  # Mark as final response, didn't hit limit
                        if self.debugging:
                            logger.info("Response sent to callback successfully")
                    else:
                        if self.debugging:
                            logger.warning("response_tool returned None despite RESPONSE being in text")
                except Exception as e:
                    logger.error(f"Error in response extraction/callback: {e}", exc_info=True)
            else:
                if self.debugging:
                    logger.info("No RESPONSE found in LLM text")
            # --- END RESPONSE tool handler ---

            # Add the assistant and user messages to the payload
            payload["messages"].append(
                {
                    "role": "assistant", 
                    "content": assistant_response
                }
            )
            payload["messages"].append(
                {
                    "role": "user", 
                    "content": meta_prompt
                }
            )

            # Exit the loop if the agent has no more requests
            if "SEARCH:" not in llm_text \
                and "RETRIEVE:" not in llm_text \
                    and "TREE:" not in llm_text \
                        and "WEIGHT:" not in llm_text \
                            and "RESPONSE" in llm_text:
                searching = False

            # Exit the loop if the agent has requested it
            if "[DONE]" in llm_text:
                searching = False
                # If DONE was used without a RESPONSE, send a fallback message
                if "RESPONSE" not in llm_text:
                    callback_fn("  :thinking_face: _Analysis complete - awaiting further instructions_", True, hit_turn_limit=False)

            turn += 1

        # If we finished without a response, send a fallback
        if searching == False and turn >= self.max_turns:
            callback_fn("  :warning: _Reached thinking limit - providing available results_", True, hit_turn_limit=True)
        
        # Update thread context cache with files Nancy looked at in this session
        if thread_ts and context_files:
            import time
            current_time = time.time()
            
            if thread_ts not in self.thread_retrievals:
                self.thread_retrievals[thread_ts] = (current_time, [])
            
            # Add new files to the thread cache and trim to last 3
            timestamp, cached_files = self.thread_retrievals[thread_ts]
            new_files = list(context_files)
            cached_files.extend(new_files)
            cached_files = cached_files[-3:]  # Keep only last 3 files
            
            # Update with new timestamp and trimmed file list
            self.thread_retrievals[thread_ts] = (current_time, cached_files)
            
            if self.debugging:
                logger.info(f"Updated thread {thread_ts} cache: {cached_files}")
            
            # Save after updating
            self._save_thread_cache()
            
            # Prune old threads (keep only 50 most recent)
            self._prune_thread_cache()

    def call_llm(self, query: str, conversation_history: list = None, thread_ts: str = None, user_id: str = None) -> str:
        """
        Process a query and return the final response.
        Collects all intermediate responses and returns the final compiled answer.
        conversation_history: list of recent messages for context
        thread_ts: Slack thread timestamp for context caching
        user_id: Slack user ID for rate limiting
        """
        # Initialize the turn variables
        payload = None
        turn = 0
        searching = True
        context_files = set()
        meta_prompt = ""
        collected_responses = []  # Collect responses during turns

        # Get the initial context (from thread cache or RAG)
        context = self.get_initial_context(query, thread_ts)

        # Construct the initial payload
        payload = self.construct_query_payload(query, context, conversation_history)

        # Loop through the turns
        while searching and turn < self.max_turns:

            # --- QUERY LLM ---
            llm_text, assistant_response = self.querry_llm(payload, turn, user_id)

            if llm_text is None:
                searching = False  # exit the loop
                raise Exception("LLM returned None")
            
            # Check if this is a rate limit response
            if "🚫 *Daily Limit Reached*" in llm_text:
                return llm_text  # Return rate limit message directly
            # --- END QUERY LLM ---

            # Begin new turn in the meta prompt
            meta_prompt += f"\n\nTURN {turn+1} REQUESTS:\n\n"

            # --- RETRIEVE tool handler ---
            file_paths = []
            if "RETRIEVE:" in llm_text:

                # Support multiple RETRIEVE: lines
                lines = llm_text.splitlines()
                for line in lines:
                    if "RETRIEVE:" in line:
                        path = line.split("RETRIEVE:")[1].strip().split()[0].rstrip("]")
                        file_paths.append(path)

                # Loop through the requested file paths
                for file_path in file_paths:
                    # Skip if file already in context
                    if file_path in context_files:
                        continue
                    else:
                        meta_prompt_addition, new_context_files = self.retrieve_tool(
                            self,
                            file_path, 
                            context_files
                        )  # Retrieves the file content for each file
                        context_files.update(new_context_files)
                        meta_prompt += meta_prompt_addition
            # --- END RETRIEVE tool handler ---

            # --- WEIGHT tool handler ---
            if "WEIGHT:" in llm_text:
                self.model_weights, meta_prompt_addition = self.weight_tool(
                    self,
                    llm_text, 
                    self.model_weights, 
                    self.model_weights_path
                ) # Updates the model weights and save them
                meta_prompt += meta_prompt_addition
            # --- END WEIGHT tool handler ---

            # --- SEARCH tool handler ---
            if "SEARCH:" in llm_text:
                meta_prompt_addition = self.search_tool(
                    self,
                    llm_text
                )  # Perform a new search if the agent has requested it
                meta_prompt += meta_prompt_addition
            # --- END SEARCH tool handler ---

            # --- TREE tool handler ---
            if "TREE:" in llm_text:
                meta_prompt_addition = self.tree_tool(
                    self,
                    llm_text
                )  # Gets the requested file tree
                meta_prompt += meta_prompt_addition
            # --- END TREE tool handler ---

            # --- RESPONSE tool handler ---
            # Extract the comment from the LLM response and collect it
            if "RESPONSE" in llm_text:
                response_text = self.response_tool(self, llm_text)
                if response_text:
                    collected_responses.append(response_text)
            # --- END RESPONSE tool handler ---

            # Add the assistant and user messages to the payload
            payload["messages"].append(
                {
                    "role": "assistant", 
                    "content": assistant_response
                }
            )
            payload["messages"].append(
                {
                    "role": "user", 
                    "content": meta_prompt
                }
            )

            # Exit the loop if the agent has no more requests
            if "SEARCH:" not in llm_text \
                and "RETRIEVE:" not in llm_text \
                    and "TREE:" not in llm_text \
                        and "WEIGHT:" not in llm_text \
                            and "RESPONSE" in llm_text:
                searching = False

            # Exit the loop if the agent has requested it
            if "[DONE]" in llm_text:
                searching = False

            turn += 1

        # Update thread context cache with files Nancy looked at in this session
        if thread_ts and context_files:
            import time
            current_time = time.time()
            
            if thread_ts not in self.thread_retrievals:
                self.thread_retrievals[thread_ts] = (current_time, [])
            
            # Add new files to the thread cache and trim to last 3
            timestamp, cached_files = self.thread_retrievals[thread_ts]
            new_files = list(context_files)
            cached_files.extend(new_files)
            cached_files = cached_files[-3:]  # Keep only last 3 files
            
            # Update with new timestamp and trimmed file list
            self.thread_retrievals[thread_ts] = (current_time, cached_files)
            
            # Save after updating
            self._save_thread_cache()
            
            # Prune old threads (keep only 50 most recent)
            self._prune_thread_cache()

        # Return the final compiled response
        if collected_responses:
            # If we have responses from the LLM turns, use the last one or combine them
            return collected_responses[-1]  # Use the most recent response
        else:
            # Fallback: ask LLM for final response if no responses were generated
            return "I apologize, but I wasn't able to generate a proper response to your question."
