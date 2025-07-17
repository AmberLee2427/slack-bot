import subprocess
import sys
from pathlib import Path

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

if __name__ == "__main__":
    test_build_pipeline_one_repo()
    print("Test completed successfully.") 