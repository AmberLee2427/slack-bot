"""
This script processes all repositories in the config/repositories.yml file.
Orchestrates the full knowledge base build pipeline (cloning, chunking, embedding).
"""

import os
import yaml
import subprocess
from pathlib import Path
import logging
import argparse

def clone_repositories(config_path: str, base_path: str = "knowledge_base/raw", dry_run: bool = False, category: str = None, force_update: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    categories = [category] if category else list(config.keys())
    for cat in categories:
        repos = config.get(cat)
        if not isinstance(repos, list):
            continue
        for repo in repos:
            repo_name = repo["name"]
            repo_url = repo["url"]
            dest_dir = Path(base_path) / cat / repo_name
            if dest_dir.exists():
                if force_update:
                    logger.info(f"Repository {cat}/{repo_name} exists. Updating...")
                    if dry_run:
                        logger.info(f"[DRY RUN] Would update {cat}/{repo_name} (git fetch & pull)")
                        continue
                    try:
                        subprocess.run(["git", "fetch", "--all"], cwd=str(dest_dir), check=True, capture_output=True, text=True)
                        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(dest_dir), capture_output=True, text=True)
                        current_branch = result.stdout.strip()
                        subprocess.run(["git", "pull", "origin", current_branch], cwd=str(dest_dir), check=True, capture_output=True, text=True)
                        logger.info(f"Successfully updated {repo_name}")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to update {repo_name}: {e.stderr}")
                else:
                    logger.info(f"Repository {cat}/{repo_name} already exists, skipping.")
            else:
                logger.info(f"Cloning {repo_name} from {repo_url} into {dest_dir}...")
                if dry_run:
                    logger.info(f"[DRY RUN] Would clone {repo_url} into {dest_dir}")
                    continue
                dest_dir.parent.mkdir(parents=True, exist_ok=True)
                try:
                    subprocess.run(
                        ["git", "clone", repo_url, str(dest_dir)],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    logger.info(f"Successfully cloned {repo_name}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to clone {repo_name}: {e.stderr}")


def chunk_repositories(config_path: str, base_path: str = "knowledge_base/raw", chunked_base: str = "knowledge_base/chunked", dry_run: bool = False, category: str = None, config_dir: str = "config") -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    Path(config_dir).mkdir(parents=True, exist_ok=True)
    categories = [category] if category else list(config.keys())
    for cat in categories:
        repos = config.get(cat)
        if not isinstance(repos, list):
            continue
        for repo in repos:
            repo_name = repo["name"]
            dest_dir = Path(base_path) / cat / repo_name
            chunked_dir = Path(chunked_base) / cat / repo_name
            if not dest_dir.exists():
                logger.warning(f"Repository directory {dest_dir} does not exist. Skipping chunking for {cat}/{repo_name}.")
                continue
            if dry_run:
                logger.info(f"[DRY RUN] Would run pyragify on {dest_dir} -> {chunked_dir}")
                continue
            config_path_out = write_pyragify_config(dest_dir, chunked_dir, config_dir, cat, repo_name)
            run_pyragify(dest_dir, chunked_dir, config_path_out, logger)


def build_pipeline(config_path: str, base_path: str = "knowledge_base/raw", chunked_base: str = "knowledge_base/chunked", dry_run: bool = False, category: str = None, force_update: bool = False, config_dir: str = "config") -> None:
    clone_repositories(config_path, base_path, dry_run, category, force_update)
    chunk_repositories(config_path, base_path, chunked_base, dry_run, category, config_dir)

def run_pyragify(repo_path, output_dir, config_path, logger):
    import subprocess
    logger.info(f"Running pyragify on {repo_path} -> {output_dir} with config {config_path}")
    try:
        subprocess.run([
            "python", "-m", "pyragify",
            "--config-file", str(config_path)
        ], check=True)
        logger.info(f"pyragify completed for {repo_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"pyragify failed for {repo_path}: {e}")

def write_pyragify_config(repo_path, output_dir, config_dir, category, repo_name):
    import yaml
    config = {
        "repo_path": str(repo_path),
        "output_dir": str(output_dir),
        "max_words": 200000,
        "max_file_size": 10485760,  # 10 MB
        "skip_patterns": [".git"],
        "skip_dirs": ["__pycache__", "node_modules"],
        "verbose": False,
    }
    config_path = Path(config_dir) / f"pyragify_{category}_{repo_name}.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    return config_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the knowledge base by cloning and chunking all repositories.")
    parser.add_argument("--config", default="config/repositories.yml", help="Path to repository configuration file")
    parser.add_argument("--base-path", default="knowledge_base/raw", help="Base path for repositories")
    parser.add_argument("--chunked-base", default="knowledge_base/chunked", help="Base path for chunked output")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--category", help="Process only a specific category")
    parser.add_argument("--force-update", action="store_true", help="Update repositories if they already exist (git pull)")
    parser.add_argument("--config-dir", default="config", help="Directory to store pyragify config files")
    args = parser.parse_args()

    build_pipeline(
        config_path=args.config,
        base_path=args.base_path,
        chunked_base=args.chunked_base,
        dry_run=args.dry_run,
        category=args.category,
        force_update=args.force_update,
        config_dir=args.config_dir
    )
