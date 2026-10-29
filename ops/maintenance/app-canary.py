"""Read-only authenticated functional check; run inside the Brain container."""

import os

import requests


def main():
    key = os.environ.get("MCP_API_KEY")
    if not key:
        raise RuntimeError("MCP_API_KEY is missing")
    session = requests.Session()
    session.headers["X-API-Key"] = key
    base = "http://127.0.0.1:8000"

    def request(method, path, **kwargs):
        response = session.request(method, base + path, timeout=90, **kwargs)
        response.raise_for_status()
        return response.json()

    hits = request("GET", "/search", params={"query": "microlensing", "limit": 1})["hits"]
    assert hits and hits[0].get("text"), "Search returned no useful result"
    doc_id = hits[0].get("id") or hits[0].get("source_document")
    assert doc_id, "Search did not identify a retrievable document"
    passage = request("POST", "/retrieve", json={"doc_id": doc_id, "window": 0})["passage"]
    assert passage.get("text", "").strip(), "Retrieval returned empty text"
    entries = request("GET", "/tree", params={"depth": 1, "max_entries": 30})["entries"]
    assert any(e.get("path") and not e["path"].startswith("unknown") for e in entries), "Tree is empty or unknown"
    print("Authenticated search, retrieval, and tree checks passed")


if __name__ == "__main__":
    main()
