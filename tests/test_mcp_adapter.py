import pytest

from bot.plugins.rag.mcp_adapter import MCPRAGAdapter, MCPAdapterError


class FakeResp:
    def __init__(self, json_data=None, status_code=200):
        self._json = json_data or {}
        self.status_code = status_code

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._json

    def raise_for_status(self):
        if not self.ok:
            raise Exception(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append(("GET", url, params))
        # search endpoint
        if url.endswith("/search"):
            return FakeResp({"hits": [{"id": "doc1", "text": "hello", "score": 1.0}]}, 200)
        # doc url endpoint
        if url.endswith("/doc/doc1/url"):
            return FakeResp({"github_url": "https://github.com/repo/doc1"}, 200)
        # embeddings/sql may be requested as POST; return 404 for get
        return FakeResp({}, 404)

    def post(self, url, json=None, timeout=None):
        self.calls.append(("POST", url, json))
        if url.endswith("/embeddings/sql"):
            # Simulate 404 to force fallback in embeddings.search
            return FakeResp({}, 404)
        if url.endswith("/retrieve"):
            # retrieve returns passage metadata
            return FakeResp({"passage": {"github_url": "https://github.com/repo/doc1"}}, 200)
        return FakeResp({}, 200)


def test_search_normalizes_fields():
    sess = FakeSession()
    adapter = MCPRAGAdapter("http://mcp.local", session=sess)
    results = adapter.search("query", limit=3)
    assert isinstance(results, list)
    assert results[0]["id"] == "doc1"
    assert results[0]["text"] == "hello"
    assert "score" in results[0]


def test_get_context_for_query_joins_text():
    sess = FakeSession()
    adapter = MCPRAGAdapter("http://mcp.local", session=sess)
    ctx = adapter.get_context_for_query("query")
    assert "hello" in ctx


def test_embeddings_search_fallback_to_search():
    sess = FakeSession()
    adapter = MCPRAGAdapter("http://mcp.local", session=sess)
    rows = adapter.embeddings.database.search("select id, text from txtai")
    # Our FakeSession.search fallback returns one row mapped from hits
    assert isinstance(rows, list)


def test_get_github_url_prefers_doc_endpoint_then_retrieve():
    sess = FakeSession()
    adapter = MCPRAGAdapter("http://mcp.local", session=sess)
    url = adapter._get_github_url("doc1")
    assert url == "https://github.com/repo/doc1"


def test_search_raises_on_bad_response():
    class BadSession(FakeSession):
        def get(self, url, params=None, timeout=None):
            return FakeResp({}, 500)

    adapter = MCPRAGAdapter("http://mcp.local", session=BadSession())
    with pytest.raises(MCPAdapterError):
        adapter.search("q")
