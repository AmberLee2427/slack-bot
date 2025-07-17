import subprocess
import sys
from pathlib import Path
import shutil

def test_pipe_real_run():
    script_path = Path(__file__).parent.parent / "scripts" / "build_knowledge_base.py"
    raw_repo = Path("knowledge_base/raw/microlens_submit")
    chunked_repo = Path("knowledge_base/chunked/microlens_submit")

    # Clean up before test (if previous runs left data)
    if raw_repo.exists():
        shutil.rmtree(raw_repo)
    if chunked_repo.exists():
        shutil.rmtree(chunked_repo)

    print("Running build_knowledge_base.py for microlens_submit (real run)...")
    result = subprocess.run([
        sys.executable, str(script_path),
        "--category", "microlens_submit",
        "--force-update"
    ])
    assert result.returncode == 0, "build_knowledge_base.py failed for microlens_submit"

    print("Checking that raw repo was cloned...")
    assert raw_repo.exists() and any(raw_repo.iterdir()), "Raw repo was not cloned!"

    print("Checking that chunked output was created...")
    assert chunked_repo.exists(), "Chunked output directory was not created!"
    txt_files = list(chunked_repo.glob('**/*.txt'))
    assert txt_files, "No chunked .txt files found!"
    print(f"Found {len(txt_files)} chunked .txt files.")

    # Clean up after test
    print("Cleaning up test output...")
    shutil.rmtree(raw_repo)
    shutil.rmtree(chunked_repo)
    print("Test completed successfully.")

if __name__ == "__main__":
    test_pipe_real_run() 