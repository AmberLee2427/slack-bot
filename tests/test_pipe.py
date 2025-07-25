import subprocess
import sys
from pathlib import Path
import shutil
import yaml
import tempfile
import argparse

def test_pipe_real_run(dirty=False):
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
    cmd = [
        sys.executable, str(script_path),
        "--category", "microlens_submit",
        "--force-update",
        "--config", str(repo_yaml),
    ]
    
    if dirty:
        cmd.append("--dirty")
        print("Using --dirty flag to keep embeddings after test")
    
    result = subprocess.run(cmd)
    assert result.returncode == 0, "build_knowledge_base.py failed for microlens_submit"

    print("Checking that raw repo was cloned...")
    assert raw_repo.exists() and any(raw_repo.iterdir()), "Raw repo was not cloned!"

    print("Checking that embeddings index was created...")
    assert embeddings_dir.exists(), "Embeddings directory was not created!"
    index_files = list(embeddings_dir.glob('**/*'))
    assert index_files, "No embeddings index files found!"
    print(f"Found {len(index_files)} embeddings index files.")

    # Clean up after test (only if not dirty)
    if not dirty:
    print("Cleaning up test output...")
    shutil.rmtree(raw_repo)
        shutil.rmtree(embeddings_dir)
    print("Test completed successfully.")
    else:
        print("Keeping embeddings for further testing (--dirty flag used)")
        print(f"Embeddings available at: {embeddings_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the knowledge base build pipeline")
    parser.add_argument("--dirty", action="store_true", help="Keep embeddings after test for further use")
    args = parser.parse_args()
    
    test_pipe_real_run(dirty=args.dirty) 