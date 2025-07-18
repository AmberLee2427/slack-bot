import subprocess
import sys
from pathlib import Path
import shutil
import yaml
import tempfile
import argparse

def inspect_chunks():
    script_path = Path(__file__).parent.parent / "scripts" / "build_knowledge_base.py"
    raw_repo = Path(__file__).parent.parent / "knowledge_base" / "raw" / "microlens_submit"
    chunked_repo = Path(__file__).parent.parent / "knowledge_base" / "chunked" / "microlens_submit"
    repo_yaml = Path(__file__).parent.parent / "config" / "repositories.yml"
    test_config_path = Path(__file__).parent / "test-config.yaml"

    # Clean up before test (if previous runs left data)
    if raw_repo.exists():
        shutil.rmtree(raw_repo)
    if chunked_repo.exists():
        shutil.rmtree(chunked_repo)

    print("Running build_knowledge_base.py for microlens_submit (real run) with test pyragify config...")
    result = subprocess.run([
        sys.executable, str(script_path),
        "--category", "microlens_submit",
        "--force-update",
        "--config", str(repo_yaml),
        "--test-pyragify-config", str(test_config_path),
    ])

def clean_test_repo():
    raw_repo = Path(__file__).parent.parent / "knowledge_base" / "raw" / "microlens_submit"
    chunked_repo = Path(__file__).parent.parent / "knowledge_base" / "chunked" / "microlens_submit"
    if raw_repo.exists():
        shutil.rmtree(raw_repo)
    if chunked_repo.exists():
        shutil.rmtree(chunked_repo)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect the chunks of a repository.")
    parser.add_argument("--clean", action="store_true", help="Clean up test repo and chunks.")
    args = parser.parse_args()

    if args.clean:
        clean_test_repo()
    else:
        inspect_chunks() 