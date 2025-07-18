import subprocess
import sys
from pathlib import Path
import shutil
import yaml
import tempfile

def test_pipe_real_run():
    script_path = Path(__file__).parent.parent / "scripts" / "build_knowledge_base.py"
    raw_repo = Path(__file__).parent.parent / "knowledge_base" / "raw" / "microlens_submit"
    embeddings_dir = Path(__file__).parent.parent / "knowledge_base" / "embeddings"
    repo_yaml = Path(__file__).parent.parent / "config" / "repositories.yml"

    # Clean up before test (if previous runs left data)
    if raw_repo.exists():
        shutil.rmtree(raw_repo)
    if embeddings_dir.exists():
        shutil.rmtree(embeddings_dir)

    print("Running build_knowledge_base.py for microlens_submit (real run)...")
    result = subprocess.run([
        sys.executable, str(script_path),
        "--category", "microlens_submit",
        "--force-update",
        "--config", str(repo_yaml),
    ])
    assert result.returncode == 0, "build_knowledge_base.py failed for microlens_submit"

    print("Checking that raw repo was cloned...")
    assert raw_repo.exists() and any(raw_repo.iterdir()), "Raw repo was not cloned!"

    print("Checking that embeddings index was created...")
    assert embeddings_dir.exists(), "Embeddings directory was not created!"
    index_files = list(embeddings_dir.glob('**/*'))
    assert index_files, "No embeddings index files found!"
    print(f"Found {len(index_files)} embeddings index files.")

    # Clean up after test
    print("Cleaning up test output...")
    shutil.rmtree(raw_repo)
    shutil.rmtree(embeddings_dir)
    print("Test completed successfully.")

if __name__ == "__main__":
    test_pipe_real_run() 