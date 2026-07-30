"""MCPRAGAdapter

Lightweight adapter that forwards RAG-style calls to an MCP server over HTTP.
This implements the small surface used by the LLM code so the rest of the bot
doesn't need to depend on txtai or other heavy embedding packages.
"""
from __future__ import annotations

import logging
import requests
from types import SimpleNamespace
from urllib.parse import quote
from typing import Optional


class MCPAdapterError(Exception):
    pass


class _EmbeddingsDB:
    def __init__(self, adapter: "MCPRAGAdapter"):
        self._adapter = adapter

    def search(self, sql: str):
        """Execute an embeddings SQL-like query against the MCP embeddings endpoint.

        Returns a list of dict rows e.g. [{'id': 'path/to/file', 'text': '...'}]
        """
        # Prefer a dedicated embeddings SQL endpoint if available
        url_sql = f"{self._adapter.base_url.rstrip('/')}/embeddings/sql"
        try:
            resp = self._adapter._session.post(url_sql, json={"sql": sql}, timeout=self._adapter.timeout)
            if resp.status_code == 404:
                raise MCPAdapterError("embeddings/sql not available")
            resp.raise_for_status()
            data = resp.json()
            return data.get("rows", [])
        except MCPAdapterError:
            # Fallback: use the search endpoint with the SQL as a natural query
            try:
                resp = self._adapter._session.get(f"{self._adapter.base_url}/search", params={"query": sql, "limit": 500}, timeout=self._adapter.timeout)
                resp.raise_for_status()
                payload = resp.json()
                hits = payload.get("hits") or payload.get("results") or payload.get("rows") or []
                # normalize to id/text
                rows = [{"id": h.get("id") or h.get("doc_id"), "text": h.get("text","")} for h in hits]
                return rows
            except Exception as exc:
                logging.getLogger(__name__).warning("Embeddings fallback search failed: %s", exc)
                raise MCPAdapterError(exc)
        except Exception as exc:
            logging.getLogger(__name__).warning("Embeddings SQL query failed: %s", exc)
            raise MCPAdapterError(exc)


class MCPRAGAdapter:
    """Adapter that exposes a RAG-like API backed by an MCP HTTP server.

    Endpoints (assumed):
      POST /search           -> {query, limit} -> {results: [{id,text,score,...}]}
      POST /context          -> {query} -> {context: str}
      GET  /doc/{doc_id}/url -> returns {github_url: str} or 404
      POST /embeddings/sql   -> {sql} -> {rows: [...]}

    The adapter normalizes responses so callers can continue using the same
    attributes they expect from the legacy RAGService.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._logger = logging.getLogger(__name__)

        if session is None:
            self._session = requests.Session()
        else:
            self._session = session

        # Set authorization header when api_key present
        if api_key:
            self._session.headers.update({"X-API-Key": api_key})
        self._session.headers.update({"Content-Type": "application/json"})

        # Provide minimal embeddings database interface expected by llm_service/tools
        self.embeddings = SimpleNamespace(database=_EmbeddingsDB(self))

    # -- Normalized API --
    def search(self, query: str, limit: int = 5):
        url = f"{self.base_url}/search"
        try:
            # Nancy HTTP API exposes GET /search?query=...&limit=...
            resp = self._session.get(url, params={"query": query, "limit": limit}, timeout=self.timeout)
            resp.raise_for_status()
            payload = resp.json()
            results = payload.get("hits") or payload.get("results") or payload.get("rows") or []
            normalized = []
            for r in results:
                data = r.get("data") if isinstance(r.get("data"), dict) else {}
                normalized.append({
                    "id": r.get("id") or r.get("doc_id"),
                    "source_document": r.get("source_document") or data.get("source_document"),
                    "text": r.get("text", ""),
                    "summary": r.get("summary") or data.get("summary"),
                    "data": data,
                    "score": float(r.get("score", 0.0)),
                    "extension_weight": float(r.get("extension_weight", 1.0)),
                    "model_score": float(r.get("model_score", 1.0)),
                    "adjusted_score": float(r.get("adjusted_score", r.get("score", 0.0)))
                })
            return normalized
        except Exception as exc:
            self._logger.error("MCP search failed: %s", exc)
            raise MCPAdapterError(exc)

    def get_context_for_query(self, query: str) -> str:
        # Nancy HTTP API doesn't provide a /context endpoint; use /search and join snippets
        try:
            results = self.search(query, limit=6)
            return "\n\n".join(r.get("text", "") for r in results)
        except Exception as exc:
            self._logger.warning("MCP get_context_for_query via search failed: %s", exc)
            raise MCPAdapterError(exc)

    def _get_github_url(self, doc_id: str) -> Optional[str]:
        # doc_id may contain slashes; quote it for URLs
        encoded = quote(doc_id, safe="")
        # Try a dedicated doc URL endpoint first
        url_doc = f"{self.base_url}/doc/{encoded}/url"
        try:
            resp = self._session.get(url_doc, timeout=self.timeout)
            if resp.status_code == 200:
                payload = resp.json()
                return payload.get("github_url")
        except Exception:
            # ignore and try retrieve endpoint
            pass

        # Fallback: use the retrieve endpoint to get passage metadata which includes github_url
        try:
            resp = self._session.post(f"{self.base_url}/retrieve", json={"doc_id": doc_id, "start": 0, "end": 1}, timeout=self.timeout)
            if resp.ok:
                payload = resp.json()
                passage = payload.get("passage") or {}
                return passage.get("github_url")
        except Exception:
            self._logger.debug("Failed to fetch github url via retrieve for %s", doc_id)

        return None

    def retrieve(self, doc_id: str, start: Optional[int] = None, end: Optional[int] = None, window: Optional[int] = None) -> dict:
        """Retrieve a document passage via MCP HTTP API.

        Args:
            doc_id: Document identifier (may include chunk suffix)
            start: 1-based start line (inclusive), optional
            end: 1-based end line (inclusive), optional
            window: chunk window size for chunk ids (optional)
        """
        url = f"{self.base_url}/retrieve"
        payload = {"doc_id": doc_id}
        if start is not None:
            payload["start"] = start
        if end is not None:
            payload["end"] = end
        if window is not None:
            payload["window"] = window
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("passage") or data
        except Exception as exc:
            self._logger.error("MCP retrieve failed: %s", exc)
            raise MCPAdapterError(exc)

    def list_tree(self, prefix: str = "", depth: int = 2, max_entries: int = 500) -> list:
        """Return a flat list of {path, type} entries from the MCP /tree endpoint."""
        url = f"{self.base_url}/tree"
        try:
            resp = self._session.get(url, params={"prefix": prefix, "depth": depth, "max_entries": max_entries}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("entries", [])
        except Exception as exc:
            self._logger.error("MCP list_tree failed: %s", exc)
            raise MCPAdapterError(exc)

    def set_weight(self, doc_id: str, multiplier: float, namespace: str = "global", ttl_days=None) -> None:
        """Push a retrieval weight multiplier to the MCP /weight endpoint."""
        url = f"{self.base_url}/weight"
        payload = {"doc_id": doc_id, "multiplier": multiplier, "namespace": namespace}
        if ttl_days is not None:
            payload["ttl_days"] = ttl_days
        try:
            resp = self._session.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except Exception as exc:
            self._logger.error("MCP set_weight failed: %s", exc)
            raise MCPAdapterError(exc)
