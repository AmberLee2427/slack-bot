import json
from pathlib import Path
import runpy
import tempfile
import unittest

HELPER = runpy.run_path(str(Path(__file__).with_name("application-records.py")))


class RecordsTests(unittest.TestCase):
    def test_absent_records(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIn("status", HELPER["collect"](Path(directory) / "missing"))

    def test_allowlist_bounding_and_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ignored-secret").write_text("do not export")
            (root / "nancy-brain-mcp.failed.log").write_text(
                "x" * 7000 + '\n{"MCP_API_KEY": "sample-value"}\nAuthorization: Bearer sample-auth\n'
            )
            result = HELPER["collect"](root)
            text = json.dumps(result)
            self.assertNotIn("sample-value", text)
            self.assertNotIn("sample-auth", text)
            self.assertNotIn("ignored-secret", text)
            self.assertLess(len(text), 6200)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "deployed-images").symlink_to("/etc/passwd")
            with self.assertRaises(OSError):
                HELPER["collect"](root)


if __name__ == "__main__":
    unittest.main()
