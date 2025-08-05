"""
This module contains the payload construction for the Gemini API.
"""

import os
from pathlib import Path
import yaml
import requests
import json
import re
import difflib
from bot.plugins.rag.rag_service import RAGService
from dotenv import load_dotenv

# environment file 
env_path = Path("bot/config/.env")
load_dotenv(env_path)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")
DEBUG_LLM = os.environ.get("DEBUG_LLM", "False").lower() in ("true", "1", "yes")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
headers = {"Content-Type": "application/json"}

class LLMService:
    def __init__(
            self, 
            system_prompt: Path = None, 
            max_turns: int = 5, 
            model_weights_path: Path = None,
            debugging: bool = None,  # Use None to read from env
            no_of_retrievals: int = 5,
            rag_service=None  # Accept existing RAG service
        ):
        # Use Nancy's base directory for all paths
        nancy_base = Path(os.environ.get("NANCY_BASE_DIR", "."))
        
        # Set default paths relative to Nancy's base
        if system_prompt is None:
            system_prompt = nancy_base / "bot/plugins/llm/system_prompt.txt"
        if model_weights_path is None:
            model_weights_path = nancy_base / "knowledge_base/embeddings/model_weights.yaml"
        
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

        # Log debugging state
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"LLM Service initialized with debugging={'ON' if self.debugging else 'OFF'}")

        # RAG variables - use provided service or create new one
        if rag_service is not None:
            self.rag = rag_service
            logger.info("Using provided RAG service")
        else:
            self.rag = RAGService()
            logger.info("Created new RAG service")
        # Build a list of all indexed file paths from the embeddings database (once)
        self.update_rag_variables()

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

    def update_rag_variables(self):
        all_indexed_docs = list(self.rag.embeddings.database.search("select id, text from txtai"))
        self.all_indexed_files = [doc['id'] for doc in all_indexed_docs]
        self.indexed_file_map = {doc['id']: doc['text'] for doc in all_indexed_docs}
    
    def update_weights(self):
        if self.model_weights_path.exists():
            with open(self.model_weights_path, "r") as f:
                self.model_weights = yaml.safe_load(f) or {}
        else:
            self.model_weights = {}

    def get_initial_context(self, query: str) -> str:
        #get the initial context
        return self.rag.get_context_for_query(query)

    def construct_query_payload(self, query: str, context: str) -> dict:
        # Compose the full prompt
        full_prompt = (
            f"{self.system_prompt}\n"
            f"\n"
            f"You will have {self.max_turns} internalturns to answer the user's question.\n"
            f"\n"
            f"User query:\n"
            f"{query}\n"
            f"\n"
            f"Relevant search results:\n"
            f"{context}\n"
        )
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": full_prompt}]}
            ]
        }

        return payload

    def querry_llm(self, payload: dict, turn: int) -> tuple[str, str]:
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Making Gemini API request for turn {turn}")
            if self.debugging:
                logger.info(f"Request payload: {json.dumps(payload, indent=2)}")
                
            response = requests.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                headers=headers,
                json=payload,
                timeout=30  # Add timeout
            )

            #save payload to file for debugging
            if self.debugging == True:
                with open(f"tests/payload_{turn}.json", "w") as f:
                    json.dump(payload, f)

            if response.ok:
                try:
                    data = response.json()
                    if self.debugging:
                        logger.info(f"Full Gemini response: {json.dumps(data, indent=2)}")
                    logger.info(f"Gemini API response received for turn {turn}")
                    llm_text = data['candidates'][0]['content']['parts'][0]['text']
                    if self.debugging:
                        logger.info(f"LLM response text: {llm_text}")
                    assistant_response = f"\n\nTURN {turn+1}:\n\n"
                    assistant_response += llm_text + "\n"
                    return llm_text, assistant_response
                except Exception as e:
                    logger.error(f"Error processing Gemini response: {e}")
                    logger.error(f"Response data: {response.text}")
                    return None, None
            else:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return None, None
        except Exception as e:
            logger.error(f"Exception in querry_llm: {e}")
            return None, None

    def call_llm_with_callback(self, query: str, callback_fn):
        """
        Process a query with a callback function for sending intermediate updates.
        callback_fn(message: str, is_final: bool = False)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Initialize the turn variables
        payload = None
        turn = 0
        searching = True
        context_files = set()
        meta_prompt = ""
        
        # Send initial status
        callback_fn("  :mag: _Searching for relevant information in knowledge base_", False)

        # Get the initial context
        logger.info("Getting initial context from RAG")
        context = self.get_initial_context(query)
        logger.info(f"RAG context length: {len(context)}")

        # Construct the initial payload
        logger.info("Constructing query payload")
        payload = self.construct_query_payload(query, context)

        # Loop through the turns
        while searching and turn < self.max_turns:
            logger.info(f"Starting LLM turn {turn}")

            # --- QUERY LLM ---
            llm_text, assistant_response = self.querry_llm(payload, turn)

            if llm_text is None:
                logger.error("LLM returned None - stopping")
                searching = False  # exit the loop
                callback_fn("  :x: _Failed to connect to Gemini API_", True)
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
                    callback_fn(f"  :page_facing_up: _Retrieving file: {file_path}_", False)
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
                callback_fn("  :mag_right: _Performing targeted search_", False)
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
                        callback_fn(response_text, True)  # Mark as final response
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
            payload["contents"].append(
                {
                    "role": "assistant", 
                    "parts": [{"text": assistant_response}]
                }
            )
            payload["contents"].append(
                {
                    "role": "user", 
                    "parts": [{"text": meta_prompt}]
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
            if "[AWAIT]" in llm_text:
                searching = False

            turn += 1

        # If we finished without a response, send a fallback
        if searching == False and turn >= self.max_turns:
            callback_fn("  :warning: _Reached thinking limit - providing available results_", True)

    def call_llm(self, query: str) -> str:
        """
        Process a query and return the final response.
        Collects all intermediate responses and returns the final compiled answer.
        """
        # Initialize the turn variables
        payload = None
        turn = 0
        searching = True
        context_files = set()
        meta_prompt = ""
        collected_responses = []  # Collect responses during turns

        # Get the initial context
        context = self.get_initial_context(query)

        # Construct the initial payload
        payload = self.construct_query_payload(query, context)

        # Loop through the turns
        while searching and turn < self.max_turns:

            # --- QUERY LLM ---
            llm_text, assistant_response = self.querry_llm(payload, turn)

            if llm_text is None:
                searching = False  # exit the loop
                raise Exception("LLM returned None")
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
            payload["contents"].append(
                {
                    "role": "assistant", 
                    "parts": [{"text": assistant_response}]
                }
            )
            payload["contents"].append(
                {
                    "role": "user", 
                    "parts": [{"text": meta_prompt}]
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
            if "[AWAIT]" in llm_text:
                searching = False

            turn += 1

        # Return the final compiled response
        if collected_responses:
            # If we have responses from the LLM turns, use the last one or combine them
            return collected_responses[-1]  # Use the most recent response
        else:
            # Fallback: ask LLM for final response if no responses were generated
            return "I apologize, but I wasn't able to generate a proper response to your question."
