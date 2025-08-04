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
from bot.plugins.rag import RAG
from dotenv import load_dotenv

# environment file 
env_path = Path("bot/config/.env")
load_dotenv(env_path)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
headers = {"Content-Type": "application/json"}

class LLM_Service:
    def __init__(
            self, 
            system_prompt: Path = Path("bot/plugins/llm/system_prompt.txt"), 
            max_turns: int = 5, 
            model_weights_path: Path = Path("knowledge_base/embeddings/model_weights.yaml"),
            debugging: bool = False,
            no_of_retrievals: int = 5
        ):
        # persisting variables
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.model_weights_path = model_weights_path
        self.debugging = debugging
        self.no_of_retrievals = no_of_retrievals
        self.update_weights()

        # RAG variables
        self.rag = RAG()
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

    def get_initial_context(self) -> str:
        #get the initial context
        return self.rag.get_context(self.query)

    def construct_query_payload(self, query: str, context: str) -> dict:
        # Compose the full prompt
        full_prompt = (
            f"{self.system_prompt}\n",
            f"\n",
            f"You will have {self.max_turns} internalturns to answer the user's question.\n",
            f"\n",
            f"User query:\n",
            f"{query}\n",
            f"\n",
            f"Relevant search results:\n",
            f"{context}\n"
        )
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": full_prompt}]}
            ]
        }

        return payload

    def querry_llm(self, payload: dict, turn: int) -> tuple[str, str]:

        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload
        )

        #save payload to file for debugging
        if self.debugging == True:
            with open(f"tests/payload_{turn}.json", "w") as f:
                json.dump(payload, f)

        if response.ok:
            data = response.json()
            llm_text = data['candidates'][0]['content']['parts'][0]['text']
            assistant_response = f"\n\nTURN {turn+1}:\n\n"
            assistant_response += llm_text + "\n"
            return llm_text, assistant_response
        else:
            return None, None

    def call_llm(self, query: str):
        # Initialize the turn variables
        payload = None
        turn = 0
        searching = True
        context_files = set()
        meta_prompt = ""

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
            self.meta_prompt = f"\n\nTURN {self.turn+1} REQUESTS:\n\n"

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
                            file_path, 
                            context_files
                        )  # Retrieves the file content for each file
                        context_files.update(new_context_files)
                        meta_prompt += meta_prompt_addition
            # --- END RETRIEVE tool handler ---

            # --- WEIGHT tool handler ---
            if "WEIGHT:" in llm_text:
                self.model_weights, meta_prompt_addition = self.weight_tool(
                    llm_text, 
                    self.model_weights, 
                    self.model_weights_path
                ) # Updates the model weights and save them
                meta_prompt += meta_prompt_addition
            # --- END WEIGHT tool handler ---

            # --- SEARCH tool handler ---
            if "SEARCH:" in llm_text:
                meta_prompt_addition = self.search_tool(
                    llm_text
                )  # Perform a new search if the agent has requested it
                meta_prompt += meta_prompt_addition
            # --- END SEARCH tool handler ---

            # --- TREE tool handler ---
            if "TREE:" in llm_text:
                meta_prompt_addition = self.tree_tool(
                    llm_text
                )  # Gets the requested file tree
                meta_prompt += meta_prompt_addition
            # --- END TREE tool handler ---

            # --- RESPONSE tool handler ---
            # Extract the comment from the LLM response and send it to Slack
            self.response_tool(llm_text)
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

            self.turn += 1
