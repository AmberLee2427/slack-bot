"""
This script processes all repositories in the config/repositories.yml file.
Orchestrates the full knowledge base build pipeline (cloning, direct txtai indexing).
"""

import os
import yaml
import subprocess
from pathlib import Path
import logging
import argparse
import json

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


def build_txtai_index(config_path: str, base_path: str = "knowledge_base/raw", embeddings_path: str = "knowledge_base/embeddings", dry_run: bool = False, category: str = None) -> None:
    """Build txtai embeddings index directly from raw files"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        from txtai.embeddings import Embeddings
    except ImportError:
        logger.error("txtai not available. Please install with: pip install txtai")
        return

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Create embeddings directory
    embeddings_dir = Path(embeddings_path)
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    # Initialize txtai embeddings
    embeddings = Embeddings({
        "path": "sentence-transformers/all-MiniLM-L6-v2",
        "content": True,
        "backend": "faiss"
    })

    # Load extension weights from YAML
    try:
        with open("config/index_weights.yaml", "r") as f:
            ext_weights = yaml.safe_load(f)
    except Exception:
        ext_weights = {}

    categories = [category] if category else list(config.keys())
    documents = []
    
    for cat in categories:
        repos = config.get(cat)
        if not isinstance(repos, list):
            continue
        for repo in repos:
            repo_name = repo["name"]
            repo_dir = Path(base_path) / cat / repo_name
            
            if not repo_dir.exists():
                logger.warning(f"Repository directory {repo_dir} does not exist. Skipping {cat}/{repo_name}.")
                continue
                
            logger.info(f"Processing {cat}/{repo_name}...")
            
            if dry_run:
                logger.info(f"[DRY RUN] Would process files in {repo_dir}")
                continue
            
            # Collect all text files
            text_files = []
            for ext in ['.py', '.md', '.txt', '.rst', '.yaml', '.yml', '.json']:
                text_files.extend(repo_dir.rglob(f"*{ext}"))
            
            # Skip common directories
            skip_dirs = {'.git', '.github', '__pycache__', 'node_modules', '.pytest_cache', '.mypy_cache'}
            text_files = [f for f in text_files if not any(skip in f.parts for skip in skip_dirs)]

            # Skip Sphinx build files and .rst.txt artifacts
            text_files = [f for f in text_files if 'docs/build' not in str(f) and not str(f).endswith('.rst.txt')]
            
            for file_path in text_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Skip empty files
                    if not content.strip():
                        continue
                    
                    # Create document ID
                    doc_id = f"{cat}/{repo_name}/{file_path.relative_to(repo_dir)}"
                    
                    # Add to documents list (no score)
                    documents.append((doc_id, content))
                    logger.debug(f"Added {doc_id} ({len(content)} chars)")
                    
                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {e}")
    
    if documents:
        logger.info(f"Indexing {len(documents)} documents...")
        if not dry_run:
            embeddings.index(documents)
            
            # Save the embeddings index
            embeddings.save(str(embeddings_dir / "index"))
            logger.info(f"Saved embeddings index to {embeddings_dir / 'index'}")
            
            # Test search
            results = embeddings.search("function", 3)
            logger.info("Test search results:")
            for result in results:
                logger.info(f"  - {result['id']}: {result['text'][:100]}...")
    else:
        logger.warning("No documents found to index")


def build_pipeline(config_path: str, base_path: str = "knowledge_base/raw", embeddings_path: str = "knowledge_base/embeddings", dry_run: bool = False, category: str = None, force_update: bool = False, dirty: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    clone_repositories(config_path, base_path, dry_run, category, force_update)
    build_txtai_index(config_path, base_path, embeddings_path, dry_run, category)
    
    if not dirty and not dry_run:
        logger.info("Cleaning up raw repositories...")
        cleanup_raw_repositories(config_path, base_path, category)
    elif dry_run and not dirty:
        logger.info("[DRY RUN] Would clean up raw repositories after processing")


def cleanup_raw_repositories(config_path: str, base_path: str = "knowledge_base/raw", category: str = None) -> None:
    """Clean up raw repositories after embeddings are built"""
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
            repo_dir = Path(base_path) / cat / repo_name
            
            if repo_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(repo_dir)
                    logger.info(f"Cleaned up {cat}/{repo_name}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {cat}/{repo_name}: {e}")
    
    # Clean up empty category directories
    base_path_obj = Path(base_path)
    if base_path_obj.exists():
        for cat_dir in base_path_obj.iterdir():
            if cat_dir.is_dir() and not any(cat_dir.iterdir()):
                try:
                    cat_dir.rmdir()
                    logger.info(f"Cleaned up empty category directory: {cat_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up empty category directory {cat_dir}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the knowledge base by cloning repositories and creating txtai embeddings.")
    parser.add_argument("--config", default="config/repositories.yml", help="Path to repository configuration file")
    parser.add_argument("--base-path", default="knowledge_base/raw", help="Base path for repositories")
    parser.add_argument("--embeddings-path", default="knowledge_base/embeddings", help="Path for embeddings index")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--category", help="Process only a specific category")
    parser.add_argument("--force-update", action="store_true", help="Update repositories if they already exist (git pull)")
    parser.add_argument("--dirty", action="store_true", help="Leave the raw repo in place after embeddings are built")

    args = parser.parse_args()

    build_pipeline(
        config_path=args.config,
        base_path=args.base_path,
        embeddings_path=args.embeddings_path,
        dry_run=args.dry_run,
        category=args.category,
        force_update=args.force_update,
        dirty=args.dirty
    )
