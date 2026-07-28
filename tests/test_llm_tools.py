from types import SimpleNamespace
from unittest.mock import patch

import yaml

from bot.plugins.llm.tools import weight_tool


class DummyRAG:
    def __init__(self):
        self.updates = []

    def set_weight(self, doc_id, multiplier):
        self.updates.append((doc_id, multiplier))


def test_weight_tool_updates_mcp_and_creates_local_record(tmp_path):
    service = SimpleNamespace(rag=DummyRAG())
    weights_path = tmp_path / "nested" / "model_weights.yaml"

    weights, prompt = weight_tool(
        service,
        "WEIGHT: docs/example.md 1.4",
        {},
        weights_path,
    )

    assert service.rag.updates == [("docs/example.md", 1.4)]
    assert weights == {"docs/example.md": 1.4}
    assert "Weighting file: docs/example.md" in prompt
    assert yaml.safe_load(weights_path.read_text()) == weights


def test_weight_tool_local_write_failure_is_nonfatal(tmp_path):
    service = SimpleNamespace(rag=DummyRAG())
    weights_path = tmp_path / "model_weights.yaml"

    with patch("pathlib.Path.open", side_effect=OSError("read-only filesystem")):
        weights, prompt = weight_tool(
            service,
            "WEIGHT: docs/example.md 0.8",
            {},
            weights_path,
        )

    assert service.rag.updates == [("docs/example.md", 0.8)]
    assert weights == {"docs/example.md": 0.8}
    assert "MCP sync failed" not in prompt
