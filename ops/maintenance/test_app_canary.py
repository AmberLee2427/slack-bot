"""Dependency-free tests for the functional deployment gate."""

import os
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class CanaryTests(unittest.TestCase):
    def check(self, responses, succeeds):
        calls = []

        def request(method, url, **kwargs):
            calls.append((method, url, kwargs))
            data = responses[len(calls) - 1]
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: data)

        session = SimpleNamespace(headers={}, request=request)
        fake = SimpleNamespace(Session=lambda: session)
        with patch.dict(sys.modules, {"requests": fake}), patch.dict(os.environ, {"MCP_API_KEY": "test"}):
            namespace = runpy.run_path(str(Path(__file__).with_name("app-canary.py")))
            if succeeds:
                namespace["main"]()
                self.assertEqual(session.headers["X-API-Key"], "test")
                self.assertEqual(len(calls), 3)
            else:
                with self.assertRaises(AssertionError):
                    namespace["main"]()

    def test_valid_chaining(self):
        self.check([
            {"hits": [{"id": "repo/file::chunk-0", "text": "result"}]},
            {"passage": {"text": "content"}},
            {"entries": [{"path": "repo/"}]},
        ], True)

    def test_empty_search_is_not_healthy(self):
        self.check([{"hits": []}], False)

    def test_empty_retrieval_is_not_healthy(self):
        self.check([{"hits": [{"id": "a", "text": "result"}]}, {"passage": {"text": ""}}], False)

    def test_unknown_tree_is_not_healthy(self):
        self.check([
            {"hits": [{"id": "a", "text": "result"}]},
            {"passage": {"text": "content"}},
            {"entries": [{"path": "unknown/"}]},
        ], False)


if __name__ == "__main__":
    unittest.main()
