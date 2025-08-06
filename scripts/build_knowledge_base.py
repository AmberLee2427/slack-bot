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
import requests
import tempfile

# Add import for nb4llm
try:
    from nb4llm import convert_ipynb_to_txt
except ImportError:
    convert_ipynb_to_txt = None

# Add import for direct Tika PDF processing
try:
    import tika
    from tika import parser as tika_parser
    TIKA_AVAILABLE = True
except ImportError:
    TIKA_AVAILABLE = False

def download_pdf_articles(config_path: str, base_path: str = "knowledge_base/raw", dry_run: bool = False, category: str = None, force_update: bool = False) -> dict:
    """Download PDF articles from URLs"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    categories = [category] if category else list(config.keys())
    
    # Track failures
    failures = {
        'failed_downloads': [],
        'skipped_existing': [],
        'successful_downloads': []
    }
    
    for cat in categories:
        articles = config.get(cat)
        if not isinstance(articles, list):
            continue
        for article in articles:
            article_name = article["name"]
            article_url = article["url"]
            dest_dir = Path(base_path) / cat
            dest_file = dest_dir / f"{article_name}.pdf"
            
            if dest_file.exists():
                if force_update:
                    logger.info(f"Article {cat}/{article_name}.pdf exists. Re-downloading...")
                    if dry_run:
                        logger.info(f"[DRY RUN] Would re-download {article_url} to {dest_file}")
                        continue
                else:
                    logger.info(f"Article {cat}/{article_name}.pdf already exists, skipping.")
                    failures['skipped_existing'].append(f"{cat}/{article_name}")
                    continue
            
            logger.info(f"Downloading {article_name} from {article_url} to {dest_file}...")
            if dry_run:
                logger.info(f"[DRY RUN] Would download {article_url} to {dest_file}")
                continue
                
            dest_dir.mkdir(parents=True, exist_ok=True)
            try:
                response = requests.get(article_url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(dest_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                logger.info(f"Successfully downloaded {article_name}")
                failures['successful_downloads'].append(f"{cat}/{article_name}")
            except Exception as e:
                logger.error(f"Failed to download {article_name}: {e}")
                failures['failed_downloads'].append(f"{cat}/{article_name}: {str(e)}")

    return failures


def clone_repositories(config_path: str, base_path: str = "knowledge_base/raw", dry_run: bool = False, category: str = None, force_update: bool = False) -> dict:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    categories = [category] if category else list(config.keys())
    
    # Track failures  
    failures = {
        'failed_clones': [],
        'failed_updates': [],
        'skipped_existing': [],
        'successful_clones': [],
        'successful_updates': []
    }
    
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
                        failures['successful_updates'].append(f"{cat}/{repo_name}")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to update {repo_name}: {e.stderr}")
                        failures['failed_updates'].append(f"{cat}/{repo_name}: {e.stderr}")
                else:
                    logger.info(f"Repository {cat}/{repo_name} already exists, skipping.")
                    failures['skipped_existing'].append(f"{cat}/{repo_name}")
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
                    failures['successful_clones'].append(f"{cat}/{repo_name}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to clone {repo_name}: {e.stderr}")
                    failures['failed_clones'].append(f"{cat}/{repo_name}: {e.stderr}")

    return failures


def build_txtai_index(config_path: str, articles_config_path: str = None, base_path: str = "knowledge_base/raw", embeddings_path: str = "knowledge_base/embeddings", dry_run: bool = False, category: str = None) -> dict:
    """Build txtai embeddings index directly from raw files and PDFs"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        from txtai.embeddings import Embeddings
    except ImportError:
        logger.error("txtai not available. Please install with: pip install txtai")
        return

    # Initialize Tika for PDF processing
    tika_ready = False
    if TIKA_AVAILABLE:
        try:
            tika.initVM()
            tika_ready = True
            logger.info("✅ Tika VM initialized for PDF processing")
        except Exception as e:
            logger.warning(f"Failed to initialize Tika VM: {e}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Load articles config if provided
    articles_config = {}
    if articles_config_path and os.path.exists(articles_config_path):
        with open(articles_config_path, "r") as f:
            articles_config = yaml.safe_load(f)
        logger.info(f"Loaded articles configuration from {articles_config_path}")

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
    
    # Track failures
    failures = {
        'failed_text_files': [],
        'failed_pdf_files': [],
        'failed_notebook_conversions': [],
        'successful_text_files': 0,
        'successful_pdf_files': 0,
        'successful_notebook_conversions': 0,
        'skipped_repositories': [],
        'skipped_articles': []
    }
    
    # Process repository files
    for cat in categories:
        repos = config.get(cat)
        if not isinstance(repos, list):
            continue
        for repo in repos:
            repo_name = repo["name"]
            repo_dir = Path(base_path) / cat / repo_name
            
            if not repo_dir.exists():
                logger.warning(f"Repository directory {repo_dir} does not exist. Skipping {cat}/{repo_name}.")
                failures['skipped_repositories'].append(f"{cat}/{repo_name}")
                continue
                
            logger.info(f"Processing {cat}/{repo_name}...")
            
            if dry_run:
                logger.info(f"[DRY RUN] Would process files in {repo_dir}")
                continue

            # --- nb4llm notebook conversion step ---
            if convert_ipynb_to_txt is not None:
                for ipynb_file in repo_dir.rglob("*.ipynb"):
                    txt_file = ipynb_file.with_suffix(".txt")
                    # Only convert if .txt does not exist or is older than .ipynb
                    if not txt_file.exists() or ipynb_file.stat().st_mtime > txt_file.stat().st_mtime:
                        try:
                            logger.info(f"Converting {ipynb_file} to {txt_file} using nb4llm...")
                            convert_ipynb_to_txt(str(ipynb_file), str(txt_file))
                            failures['successful_notebook_conversions'] += 1
                        except Exception as e:
                            logger.warning(f"Failed to convert {ipynb_file} to txt: {e}")
                            failures['failed_notebook_conversions'].append(f"{ipynb_file}: {str(e)}")
            else:
                logger.warning("nb4llm not available. Skipping notebook conversion.")
            # --- end nb4llm notebook conversion step ---

            # Collect all text files (including .ipynb and .txt)
            text_files = []
            for ext in ['.py', '.md', '.txt', '.rst', '.yaml', '.yml', '.json', '.ipynb']:
                text_files.extend(repo_dir.rglob(f"*{ext}"))
            
            # Collect PDF files from repositories if Tika is available
            pdf_files = []
            if tika_ready:
                pdf_files.extend(repo_dir.rglob("*.pdf"))
            
            # Skip common directories for both text and PDF files
            skip_dirs = {'.git', '.github', '__pycache__', 'node_modules', '.pytest_cache', '.mypy_cache'}
            text_files = [f for f in text_files if not any(skip in f.parts for skip in skip_dirs)]
            pdf_files = [f for f in pdf_files if not any(skip in f.parts for skip in skip_dirs)]

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
                    failures['successful_text_files'] += 1
                    
                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {e}")
                    failures['failed_text_files'].append(f"{file_path}: {str(e)}")
            
            # Process PDF files found in repository
            for pdf_path in pdf_files:
                try:
                    # Extract text from PDF using direct Tika parser
                    parsed = tika_parser.from_file(str(pdf_path))
                    content = parsed.get('content', '') if parsed else ''
                    
                    if content and len(content.strip()) > 100:
                        # Create document ID
                        doc_id = f"{cat}/{repo_name}/{pdf_path.relative_to(repo_dir)}"
                        
                        # Add metadata to content
                        metadata = f"Source: Repository PDF from {repo['url']}\nPath: {pdf_path.relative_to(repo_dir)}\nType: Repository Document\n\n"
                        full_content = metadata + content.strip()
                        
                        # Add to documents list
                        documents.append((doc_id, full_content))
                        logger.info(f"Added repository PDF {doc_id} ({len(content)} chars)")
                        failures['successful_pdf_files'] += 1
                    else:
                        logger.warning(f"Failed to extract meaningful text from repository PDF {pdf_path}")
                        failures['failed_pdf_files'].append(f"{pdf_path}: No meaningful text extracted")
                        
                except Exception as e:
                    logger.error(f"Error processing repository PDF {pdf_path}: {e}")
                    failures['failed_pdf_files'].append(f"{pdf_path}: {str(e)}")
    
    # Process PDF articles
    article_categories = [category] if category else list(articles_config.keys())
    for cat in article_categories:
        articles = articles_config.get(cat)
        if not isinstance(articles, list):
            continue
        for article in articles:
            article_name = article["name"]
            pdf_file = Path(base_path) / cat / f"{article_name}.pdf"
            
            if not pdf_file.exists():
                logger.warning(f"PDF file {pdf_file} does not exist. Skipping {cat}/{article_name}.")
                failures['skipped_articles'].append(f"{cat}/{article_name}")
                continue
                
            logger.info(f"Processing PDF {cat}/{article_name}...")
            
            if dry_run:
                logger.info(f"[DRY RUN] Would process PDF {pdf_file}")
                continue

            if tika_ready:
                try:
                    # Extract text from PDF using direct Tika parser
                    parsed = tika_parser.from_file(str(pdf_file))
                    content = parsed.get('content', '') if parsed else ''
                    
                    if content and len(content.strip()) > 100:
                        # Create document ID
                        doc_id = f"journal_articles/{cat}/{article_name}"
                        
                        # Add metadata to content
                        metadata = f"Title: {article['description']}\nSource: {article.get('url', 'Unknown')}\nType: Journal Article\n\n"
                        full_content = metadata + content.strip()
                        
                        # Add to documents list
                        documents.append((doc_id, full_content))
                        logger.info(f"Added PDF {doc_id} ({len(content)} chars)")
                        failures['successful_pdf_files'] += 1
                    else:
                        logger.warning(f"Failed to extract meaningful text from {pdf_file}")
                        failures['failed_pdf_files'].append(f"{pdf_file}: No meaningful text extracted")
                        
                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_file}: {e}")
                    failures['failed_pdf_files'].append(f"{pdf_file}: {str(e)}")
            else:
                logger.warning(f"Tika not available. Skipping PDF {pdf_file}")
                failures['failed_pdf_files'].append(f"{pdf_file}: Tika not available")
    
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

    return failures


def build_pipeline(config_path: str, articles_config_path: str = None, base_path: str = "knowledge_base/raw", embeddings_path: str = "knowledge_base/embeddings", dry_run: bool = False, category: str = None, force_update: bool = False, dirty: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Track all failures across stages
    all_failures = {
        'repos': {},
        'articles': {},
        'indexing': {}
    }
    
    # Clone repositories
    repo_failures = clone_repositories(config_path, base_path, dry_run, category, force_update)
    all_failures['repos'] = repo_failures
    
    # Download PDF articles if config provided
    if articles_config_path and os.path.exists(articles_config_path):
        article_failures = download_pdf_articles(articles_config_path, base_path, dry_run, category, force_update)
        all_failures['articles'] = article_failures
    elif articles_config_path:
        logger.warning(f"Articles config file {articles_config_path} not found. Skipping PDF downloads.")
    
    # Build embeddings index including both repos and PDFs
    indexing_failures = build_txtai_index(config_path, articles_config_path, base_path, embeddings_path, dry_run, category)
    all_failures['indexing'] = indexing_failures
    
    # Cleanup downloaded files
    if not dirty and not dry_run:
        logger.info("Cleaning up raw repositories and PDFs...")
        cleanup_raw_repositories(config_path, base_path, category)
        if articles_config_path and os.path.exists(articles_config_path):
            cleanup_pdf_articles(articles_config_path, base_path, category)
    elif dry_run and not dirty:
        logger.info("[DRY RUN] Would clean up raw repositories and PDFs after processing")
    
    # Print comprehensive summary
    print_pipeline_summary(all_failures, dry_run)


def print_pipeline_summary(all_failures: dict, dry_run: bool = False) -> None:
    """Print a comprehensive summary of the pipeline execution"""
    logger = logging.getLogger(__name__)
    
    prefix = "[DRY RUN] " if dry_run else ""
    
    logger.info("=" * 60)
    logger.info(f"{prefix}KNOWLEDGE BASE PIPELINE SUMMARY")
    logger.info("=" * 60)
    
    # Repository summary
    repo_failures = all_failures.get('repos', {})
    if repo_failures:
        logger.info("\n📁 REPOSITORIES:")
        if repo_failures.get('successful_clones'):
            logger.info(f"  ✅ Successfully cloned: {len(repo_failures['successful_clones'])}")
            for repo in repo_failures['successful_clones']:
                logger.info(f"     - {repo}")
        
        if repo_failures.get('successful_updates'):
            logger.info(f"  🔄 Successfully updated: {len(repo_failures['successful_updates'])}")
            for repo in repo_failures['successful_updates']:
                logger.info(f"     - {repo}")
        
        if repo_failures.get('skipped_existing'):
            logger.info(f"  ⏭️  Skipped (already exists): {len(repo_failures['skipped_existing'])}")
            
        if repo_failures.get('failed_clones'):
            logger.info(f"  ❌ Failed to clone: {len(repo_failures['failed_clones'])}")
            for failure in repo_failures['failed_clones']:
                logger.info(f"     - {failure}")
                
        if repo_failures.get('failed_updates'):
            logger.info(f"  ❌ Failed to update: {len(repo_failures['failed_updates'])}")
            for failure in repo_failures['failed_updates']:
                logger.info(f"     - {failure}")
    
    # Articles summary
    article_failures = all_failures.get('articles', {})
    if article_failures:
        logger.info("\n📚 PDF ARTICLES:")
        if article_failures.get('successful_downloads'):
            logger.info(f"  ✅ Successfully downloaded: {len(article_failures['successful_downloads'])}")
            for article in article_failures['successful_downloads']:
                logger.info(f"     - {article}")
        
        if article_failures.get('skipped_existing'):
            logger.info(f"  ⏭️  Skipped (already exists): {len(article_failures['skipped_existing'])}")
            
        if article_failures.get('failed_downloads'):
            logger.info(f"  ❌ Failed to download: {len(article_failures['failed_downloads'])}")
            for failure in article_failures['failed_downloads']:
                logger.info(f"     - {failure}")
    
    # Indexing summary
    indexing_failures = all_failures.get('indexing', {})
    if indexing_failures:
        logger.info("\n🔍 INDEXING & EMBEDDING:")
        
        # Successes
        text_files = indexing_failures.get('successful_text_files', 0)
        pdf_files = indexing_failures.get('successful_pdf_files', 0)
        notebooks = indexing_failures.get('successful_notebook_conversions', 0)
        
        if text_files > 0:
            logger.info(f"  ✅ Successfully indexed text files: {text_files}")
        if pdf_files > 0:
            logger.info(f"  ✅ Successfully indexed PDF files: {pdf_files}")
        if notebooks > 0:
            logger.info(f"  ✅ Successfully converted notebooks: {notebooks}")
        
        # Skipped
        if indexing_failures.get('skipped_repositories'):
            logger.info(f"  ⏭️  Skipped repositories (not found): {len(indexing_failures['skipped_repositories'])}")
            for repo in indexing_failures['skipped_repositories']:
                logger.info(f"     - {repo}")
                
        if indexing_failures.get('skipped_articles'):
            logger.info(f"  ⏭️  Skipped articles (not found): {len(indexing_failures['skipped_articles'])}")
            for article in indexing_failures['skipped_articles']:
                logger.info(f"     - {article}")
        
        # Failures
        if indexing_failures.get('failed_text_files'):
            logger.info(f"  ❌ Failed to process text files: {len(indexing_failures['failed_text_files'])}")
            for failure in indexing_failures['failed_text_files']:
                logger.info(f"     - {failure}")
                
        if indexing_failures.get('failed_pdf_files'):
            logger.info(f"  ❌ Failed to process PDF files: {len(indexing_failures['failed_pdf_files'])}")
            for failure in indexing_failures['failed_pdf_files']:
                logger.info(f"     - {failure}")
                
        if indexing_failures.get('failed_notebook_conversions'):
            logger.info(f"  ❌ Failed notebook conversions: {len(indexing_failures['failed_notebook_conversions'])}")
            for failure in indexing_failures['failed_notebook_conversions']:
                logger.info(f"     - {failure}")
    
    # Overall status
    total_failures = (
        len(repo_failures.get('failed_clones', [])) +
        len(repo_failures.get('failed_updates', [])) +
        len(article_failures.get('failed_downloads', [])) +
        len(indexing_failures.get('failed_text_files', [])) +
        len(indexing_failures.get('failed_pdf_files', [])) +
        len(indexing_failures.get('failed_notebook_conversions', []))
    )
    
    logger.info("\n" + "=" * 60)
    if total_failures == 0:
        logger.info(f"{prefix}✅ PIPELINE COMPLETED SUCCESSFULLY - No failures detected!")
    else:
        logger.info(f"{prefix}⚠️  PIPELINE COMPLETED WITH {total_failures} FAILURES")
        logger.info("Check the detailed failure list above for specific issues.")
    logger.info("=" * 60)


def cleanup_pdf_articles(articles_config_path: str, base_path: str = "knowledge_base/raw", category: str = None) -> None:
    """Clean up downloaded PDF articles after embeddings are built"""
    logger = logging.getLogger(__name__)
    
    with open(articles_config_path, "r") as f:
        config = yaml.safe_load(f)
    
    categories = [category] if category else list(config.keys())
    for cat in categories:
        articles = config.get(cat)
        if not isinstance(articles, list):
            continue
        for article in articles:
            article_name = article["name"]
            pdf_file = Path(base_path) / cat / f"{article_name}.pdf"
            
            if pdf_file.exists():
                try:
                    pdf_file.unlink()
                    logger.info(f"Cleaned up PDF {cat}/{article_name}.pdf")
                except Exception as e:
                    logger.warning(f"Failed to clean up PDF {cat}/{article_name}.pdf: {e}")
    
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
    parser = argparse.ArgumentParser(description="Build the knowledge base by cloning repositories, downloading PDFs, and creating txtai embeddings.")
    parser.add_argument("--config", default="config/repositories.yml", help="Path to repository configuration file")
    parser.add_argument("--articles-config", default="config/articles.yml", help="Path to PDF articles configuration file")
    parser.add_argument("--base-path", default="knowledge_base/raw", help="Base path for repositories and PDFs")
    parser.add_argument("--embeddings-path", default="knowledge_base/embeddings", help="Path for embeddings index")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--category", help="Process only a specific category")
    parser.add_argument("--force-update", action="store_true", help="Update repositories and re-download PDFs if they already exist")
    parser.add_argument("--dirty", action="store_true", help="Leave the raw repos and PDFs in place after embeddings are built")

    args = parser.parse_args()

    build_pipeline(
        config_path=args.config,
        articles_config_path=args.articles_config,
        base_path=args.base_path,
        embeddings_path=args.embeddings_path,
        dry_run=args.dry_run,
        category=args.category,
        force_update=args.force_update,
        dirty=args.dirty
    )
