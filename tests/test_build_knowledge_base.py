#! /usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import subprocess
import tempfile
import shutil
import os

def test_build_pipeline_one_repo():
    # Only process the 'microlens_submit' repo in the 'microlens_submit' category
    script_path = Path(__file__).parent.parent / "scripts" / "build_knowledge_base.py"
    result = subprocess.run([
        sys.executable, str(script_path),
        "--category", "microlens_submit",
        "--force-update",
        "--dry-run"  # Remove this flag to actually run
    ])
    assert result.returncode == 0, "build_knowledge_base.py failed for microlens_submit"


def test_nb4llm_conversion_in_pipeline():
    import yaml
    from scripts.build_knowledge_base import build_txtai_index
    from pathlib import Path
    import sys

    # Setup temp repo structure
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "raw"
        repo_dir = base_path / "notebooks" / "roman_tools"
        repo_dir.mkdir(parents=True, exist_ok=True)
        ipynb_path = repo_dir / "Getting Started.ipynb"
        # Copy the sample notebook into the temp repo
        src_ipynb = Path(__file__).parent.parent / "knowledge_base" / "raw" / "jupyter_notebooks" / "roman_tools" / "notebooks" / "Getting Started.ipynb"
        shutil.copy(src_ipynb, ipynb_path)

        # Create a minimal config file
        config = {"notebooks": [{"name": "roman_tools", "url": "https://example.com/roman_tools.git"}]}
        config_path = Path(tmpdir) / "repositories.yml"
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f)

        # Run the txtai index build (will trigger nb4llm conversion)
        build_txtai_index(str(config_path), str(base_path), embeddings_path=str(Path(tmpdir) / "embeddings"), dry_run=False, category="notebooks")

        # Check that the .txt file was created
        txt_path = ipynb_path.with_suffix(".txt")
        assert txt_path.exists(), f"Converted .txt file not found: {txt_path}"
        with open(txt_path) as f:
            txt_content = f.read()
        assert '```markdown' in txt_content and '```python' in txt_content, "Converted .txt file does not contain expected fenced blocks"
        assert '# Getting Started.ipynb' in txt_content, "Notebook name header missing in .txt file"

if __name__ == "__main__":
    test_build_pipeline_one_repo()
    test_nb4llm_conversion_in_pipeline()
    print("All tests completed successfully.") 