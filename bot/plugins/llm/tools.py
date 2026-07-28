"""
This file contains the tools for the LLM.
"""

import re
import difflib
import logging
from pathlib import Path
import yaml
import os


def search_tool(self, llm_text: str, callback_fn=None) -> str:
    """
    This function handles the SEARCH tool.
    It extracts the search query from the LLM response and updates the meta prompt.
    """
    meta_prompt = ""

    def _strip_chunk_suffix(doc_id: str) -> str:
        return re.sub(r"::chunk-\d+$", "", doc_id or "")

    def _get_summary_for_result(result: dict) -> str | None:
        # Prefer summary provided by the backend
        summary = result.get("summary")
        if summary:
            return summary

        # If the result is itself a summary document, use its text
        doc_id = result.get("id") or ""
        if doc_id.startswith("summaries/"):
            return result.get("text", "")

        # Try to map to summaries/{source_document} from the local index map
        base_doc_id = result.get("source_document") or _strip_chunk_suffix(doc_id)
        if base_doc_id:
            summary_doc_id = f"summaries/{base_doc_id}"
            if summary_doc_id in getattr(self, "indexed_file_map", {}):
                return self.indexed_file_map.get(summary_doc_id)

        return None

    lines = llm_text.splitlines()
    for line in lines:
        if "SEARCH:" in line:
            search_content = line.split("SEARCH:")[1].strip()
            raw_query = search_content

            # Show search context
            if callback_fn:
                callback_fn(f"  🔍 _Searching for: {raw_query}_", False)

            if raw_query.lower().startswith("select"):
                query_part = raw_query
                results = list(self.rag.embeddings.database.search(query_part))
            else:
                # For natural language queries, expect format: <query> limit N
                parts = raw_query.split()
                llm_search_max_results = (
                    int(parts[-1]) if parts[-1].isdigit() else self.no_of_retrievals
                )
                # Remove the trailing ' limit N' (8 chars) from the end
                query_part = raw_query[:-8]
                results = self.rag.search(query_part, limit=llm_search_max_results)

            # Remove redundant "Found X sources" message
            # if callback_fn and results:
            #     callback_fn(f"  📊 Found {len(results)} relevant sources", False)  # REMOVED

            # Update the context for the next turn
            meta_prompt += f"\n\nSearch results:\n{query_part}\n"
            for i, result in enumerate(results, 1):
                github_url = self.rag._get_github_url(result["id"])
                data = (
                    result.get("data") if isinstance(result.get("data"), dict) else {}
                )
                if github_url:
                    slack_link = f"<{github_url}|{Path(result['id']).name}>"
                    meta_prompt += f"\n\nResult {i}:\n"
                    meta_prompt += f"  File: {result['id']} ({slack_link})\n"
                else:
                    meta_prompt += f"\n\nResult {i}:\n"
                    meta_prompt += f"  File: {result['id']}\n"
                if data:
                    line_start = data.get("line_start")
                    line_end = data.get("line_end")
                    chunk_index = data.get("chunk_index")
                    chunk_count = data.get("chunk_count")
                    if line_start is not None and line_end is not None:
                        meta_prompt += f"  Lines: {line_start}-{line_end}\n"
                    if chunk_index is not None and chunk_count is not None:
                        meta_prompt += (
                            f"  Chunk: {int(chunk_index) + 1}/{chunk_count}\n"
                        )
                meta_prompt += f"  Score: {result.get('score', 0.0):.3f}\n"
                meta_prompt += (
                    f"  Extension weight: {result.get('extension_weight', 1.0):.3f}\n"
                )
                meta_prompt += f"  Model weight: {result.get('model_score', 1.0):.3f}\n"
                meta_prompt += f"  Final score: {result.get('adjusted_score', result.get('score', 0.0)):.3f}\n"
                meta_prompt += f"  Content length: {len(result['text'])} chars\n"
                summary_text = _get_summary_for_result(result)
                if summary_text:
                    summary_text = summary_text.strip()
                    if len(summary_text) > 600:
                        summary_text = summary_text[:600] + "..."
                    meta_prompt += f"  Summary: {summary_text}\n"
                meta_prompt += f"  Content: {result['text']}"

    return meta_prompt


def tree_tool(self, llm_text: str):
    """
    This function handles the TREE tool.
    Delegates to the MCP /tree endpoint so filtering and index-reading
    stay in one place (server-side).
    """
    meta_prompt = ""
    lines = llm_text.splitlines()
    for line in lines:
        if "TREE:" in line:
            tree_dir = line.split("TREE:")[1].strip().split()[0].rstrip("]")
            tree_dir = tree_dir.rstrip("/")
            prefix = tree_dir + "/" if tree_dir else ""
            try:
                entries = self.rag.list_tree(prefix=prefix, depth=3)
                if entries:
                    lines_out = []
                    for e in entries:
                        path = e.get("path", "")
                        # Show path relative to the requested prefix
                        rel = (
                            path[len(prefix) :]
                            if prefix and path.startswith(prefix)
                            else path
                        )
                        if not rel:
                            continue
                        if e.get("type") in ("dir", "directory"):
                            lines_out.append(f"[DIR] {rel}/")
                        else:
                            lines_out.append(f"      {rel}")
                    if lines_out:
                        meta_prompt += (
                            f"\n\nTREE: Listing for '{tree_dir}':\n"
                            + "\n".join(lines_out)
                        )
                    else:
                        meta_prompt += f"\n\nTREE: Directory '{tree_dir}' not found or empty in index."
                else:
                    meta_prompt += (
                        f"\n\nTREE: Directory '{tree_dir}' not found or empty in index."
                    )
            except Exception as exc:
                meta_prompt += f"\n\nTREE: Error listing '{tree_dir}': {exc}"

    return meta_prompt


def weight_tool(
    self, llm_text: str, model_weights: dict, model_weights_path: str
) -> tuple[dict, str]:
    """
    This function handles the WEIGHT tool.
    Forwards weight updates to the MCP server so they actually affect search results.
    """
    lines = llm_text.splitlines()
    meta_prompt = f"\n\nModel reweighting:"
    for line in lines:
        if "WEIGHT:" in line:
            parts = line.split("WEIGHT:")[1].strip().split()
            path = parts[0].rstrip("]")
            score_multiplier = float(parts[1].rstrip("]")) if len(parts) > 1 else 1.0
            model_weights[path] = score_multiplier
            # Forward to MCP server so weights take effect server-side
            if getattr(self, "rag", None) and hasattr(self.rag, "set_weight"):
                try:
                    self.rag.set_weight(doc_id=path, multiplier=score_multiplier)
                    meta_prompt += (
                        f"\nWeighting file: {path} with multiplier: {score_multiplier}"
                    )
                except Exception as exc:
                    meta_prompt += f"\nWeighting file: {path} with multiplier: {score_multiplier} (MCP sync failed: {exc})"
            else:
                meta_prompt += (
                    f"\nWeighting file: {path} with multiplier: {score_multiplier}"
                )

    # MCP owns the live weights. Keep a best-effort local audit copy without
    # failing the user's request if the container's persistence path is broken.
    try:
        weights_path = Path(model_weights_path)
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        with weights_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(model_weights, f)
    except OSError as exc:
        logging.getLogger(__name__).warning(
            "Could not persist local model weights to %s: %s",
            model_weights_path,
            exc,
        )

    return model_weights, meta_prompt


def retrieve_tool(self, file_path: str, context_files: set) -> tuple[str, set]:
    """
    This function handles the RETRIEVE tool.
    It extracts the file path(s) from the LLM response and retrieves the file content.
    """
    meta_prompt = ""
    new_context_files = set()

    def _parse_retrieve_spec(spec: str):
        parts = spec.split()
        if not parts:
            return None, None, None, None
        path = parts[0]
        start = None
        end = None
        window = None
        for tok in parts[1:]:
            if tok.startswith("start="):
                try:
                    start = int(tok.split("=", 1)[1])
                except Exception:
                    pass
            elif tok.startswith("end="):
                val = tok.split("=", 1)[1]
                if val.lower() in ("eof", "full", "all"):
                    end = None
                else:
                    try:
                        end = int(val)
                    except Exception:
                        pass
            elif tok.startswith("lines="):
                val = tok.split("=", 1)[1]
                if "-" in val:
                    try:
                        start_str, end_str = val.split("-", 1)
                        start = int(start_str)
                        end = int(end_str)
                    except Exception:
                        pass
            elif tok.startswith("window="):
                try:
                    window = int(tok.split("=", 1)[1])
                except Exception:
                    pass
            elif re.match(r"^\d+-\d+$", tok):
                try:
                    start_str, end_str = tok.split("-", 1)
                    start = int(start_str)
                    end = int(end_str)
                except Exception:
                    pass
        return path, start, end, window

    # Exact match in indexed files
    # Try MCP retrieve if available
    if getattr(self, "rag", None) and hasattr(self.rag, "retrieve"):
        try:
            spec_path, start, end, window = _parse_retrieve_spec(file_path)
            if spec_path:
                file_path = spec_path
            passage = self.rag.retrieve(file_path, start=start, end=end, window=window)
            if passage:
                github_url = passage.get("github_url") or self.rag._get_github_url(
                    file_path
                )
                file_content = passage.get("text", "")
                if github_url:
                    slack_link = f"<{github_url}|{Path(file_path).name}>"
                    file_content += f"\n\nGitHub URL: {slack_link}"
                line_start = passage.get("start") or passage.get("line_start")
                line_end = passage.get("end") or passage.get("line_end")
                total_lines = passage.get("total_lines")
                if line_start is not None or line_end is not None:
                    range_text = f"Lines: {line_start}-{line_end if line_end is not None else 'EOF'}"
                    if total_lines:
                        range_text += f" / {total_lines}"
                    meta_prompt += f"\n\nRetrieved file: {file_path}\n{range_text}\nFile content:\n{file_content}"
                else:
                    meta_prompt += f"\n\nRetrieved file: {file_path}\nFile content:\n{file_content}"
                new_context_files.add(file_path)
                return meta_prompt, new_context_files
        except Exception:
            # Fall back to local index below
            pass

    matching_chunks = [
        doc_id for doc_id in self.all_indexed_files if doc_id == file_path
    ]
    if matching_chunks:
        for chunk_id in matching_chunks:
            file_content = "\n\n".join(
                self.indexed_file_map[chunk_id] for chunk_id in matching_chunks
            )
            github_url = self.rag._get_github_url(matching_chunks[0])
            if github_url:
                slack_link = f"<{github_url}|{Path(matching_chunks[0]).name}>"
                file_content += f"\n\nGitHub URL: {slack_link}"
            meta_prompt += (
                f"\n\nRetrieved file: {file_path}\nFile content:\n{file_content}"
            )
        # Add to context_files to prevent future duplicates
        new_context_files.update(matching_chunks)

    else:
        # Suggest similar indexed files
        suggestions = difflib.get_close_matches(
            file_path, self.all_indexed_files, n=5, cutoff=0.6
        )
        if suggestions:
            meta_prompt += f"\n\nDid you mean: {', '.join(suggestions)}"
        file_content = f"[File not found in index. Searched: {file_path}]"
        meta_prompt += f"\n\nRetrieved file: {file_path}\nFile content:\n{file_content}"

    return meta_prompt, new_context_files


def response_tool(self, llm_text: str) -> str:
    """
    This function handles the response from the LLM.
    It extracts the comment from the LLM response and returns it for the bot to send.
    """
    import logging

    logger = logging.getLogger(__name__)

    # RESPONSE tool handler
    # Extract the comment from the LLM response
    # [BEGIN RESPONSE]
    # <comment>
    # [END RESPONSE]
    if self.debugging:
        logger.info(f"response_tool called with text length: {len(llm_text)}")
        logger.info(f"Looking for pattern [BEGIN RESPONSE]...[END RESPONSE]")

    match = re.search(r"\[BEGIN RESPONSE\](.*?)\[END RESPONSE\]", llm_text, re.DOTALL)
    if match:
        response_text = match.group(1).strip()
        if self.debugging:
            logger.info(f"Found response match: '{response_text}'")
        return response_text
    else:
        if self.debugging:
            logger.warning("No [BEGIN RESPONSE]...[END RESPONSE] pattern found in text")
        return None
