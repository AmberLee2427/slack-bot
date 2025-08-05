"""
RAG (Retrieval-Augmented Generation) service for the Slack bot.
Provides semantic search capabilities using txtai embeddings.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class RAGService:
    """Service for retrieving relevant context from the knowledge base."""
    
    def __init__(self, embeddings_path: str = "knowledge_base/embeddings/index", config_path: str = "config/repositories.yml"):
        """
        Initialize the RAG service.
        
        Args:
            embeddings_path: Path to the txtai embeddings index
            config_path: Path to the repositories configuration file
        """
        # Use Nancy's base directory from environment variable
        nancy_base = Path(os.environ.get("NANCY_BASE_DIR", "."))
        self.embeddings_path = nancy_base / embeddings_path
        self.config_path = nancy_base / config_path
        self.embeddings = None
        self.repo_config = None
        self._load_config()
        self._load_embeddings()
        self.model_weights_path = Path(embeddings_path).parent / "model_weights.yaml"
        self.model_weights = self._load_model_weights()
        self.extension_weights = self._load_extension_weights()
    
    def _load_config(self):
        """Load the repositories configuration."""
        try:
            with open(self.config_path, 'r') as f:
                self.repo_config = yaml.safe_load(f)
            logger.info(f"Loaded repository configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load repository configuration: {e}")
            self.repo_config = {}
    
    def _get_github_url(self, doc_id: str) -> Optional[str]:
        """
        Convert a document ID to a GitHub URL.
        
        Args:
            doc_id: Document ID in format "category/repo_name/path/to/file"
            
        Returns:
            GitHub URL or None if not found
        """
        if not self.repo_config:
            return None
            
        parts = doc_id.split('/', 2)  # Split into category, repo_name, file_path
        if len(parts) < 3:
            return None
            
        category, repo_name, file_path = parts
        
        # Find the repository in config
        if category in self.repo_config:
            for repo in self.repo_config[category]:
                if repo['name'] == repo_name:
                    # Convert GitHub URL to blob URL
                    github_url = repo['url']
                    if github_url.endswith('.git'):
                        github_url = github_url[:-4]
                    return f"{github_url}/blob/main/{file_path}"
        
        return None
    
    def _load_embeddings(self):
        """Load the txtai embeddings index."""
        try:
            from txtai.embeddings import Embeddings
            
            if not self.embeddings_path.exists():
                logger.warning(f"Embeddings index not found at {self.embeddings_path}")
                logger.info("Run the knowledge base build script first:")
                logger.info("python scripts/build_knowledge_base.py --category microlens_submit --dirty")
                return
            
            logger.info(f"Loading embeddings from {self.embeddings_path}")
            self.embeddings = Embeddings()
            self.embeddings.load(str(self.embeddings_path))
            logger.info("Embeddings loaded successfully")
            
        except ImportError:
            logger.error("txtai not available. Please install with: pip install txtai")
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
    
    def _load_model_weights(self):
        if self.model_weights_path.exists():
            try:
                with open(self.model_weights_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load model weights: {e}")
        return {}
    
    def _load_extension_weights(self):
        weights_path = Path(__file__).parent.parent / "config/weights.yaml"
        if weights_path.exists():
            try:
                with open(weights_path, "r") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load weights: {e}")
        return {}
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of dictionaries with 'id', 'text', and 'score' keys
        """
        if not self.embeddings:
            logger.warning("Embeddings not loaded, cannot perform search")
            return []
        
        try:
            results = self.embeddings.search(query, limit * 50)  # much larger candidate pool for reweighting
            # Convert to list of dicts for easier handling
            formatted_results = []
            # Load weights config
            weights_cfg = self.extension_weights or {}
            ext_weights = weights_cfg.get('extensions', {})
            path_includes = weights_cfg.get('path_includes', {})
            for result in results:
                doc_id = result['id']
                ext = Path(doc_id).suffix
                weight = ext_weights.get(ext, 1.0)
                doc_id_lower = doc_id.lower()
                for keyword, mult in path_includes.items():
                    if keyword.lower() in doc_id_lower:
                        weight *= mult
                # Model weight
                model_score = self.model_weights.get(doc_id, 1.0)
                try:
                    model_score = float(model_score)
                except Exception:
                    model_score = 1.0
                model_score = max(0.5, min(model_score, 2.0))
                adjusted_score = weight * model_score * result.get('score', 0.0)
                #print(f"doc_id: {doc_id}, raw_score: {result.get('score', 0.0)}, weight: {weight}, model_score: {model_score}, adjusted_score: {adjusted_score}")
                formatted_results.append({
                    'id': doc_id,
                    'text': result['text'],
                    'score': result.get('score', 0.0),
                    'extension_weight': weight,
                    'model_score': model_score,
                    'adjusted_score': adjusted_score
                })
            # Sort by adjusted_score, descending
            formatted_results.sort(key=lambda r: r['adjusted_score'], reverse=True)
            logger.info(f"Found {len(formatted_results)} results for query: '{query}' (sorted by adjusted_score)")
            return formatted_results[:limit]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_context_for_query(self, query: str, max_chars: int = 4000) -> str:
        """
        Get formatted context for a query, suitable for LLM prompts.
        
        Args:
            query: Search query
            max_chars: Maximum characters to include in context
            
        Returns:
            Formatted context string
        """
        results = self.search(query, limit=5)
        
        if not results:
            return "No relevant information found."
        
        context_parts = []
        current_length = 0
        
        for result in results:
            # Get GitHub URL for this document
            github_url = self._get_github_url(result['id'])
            
            # Truncate text if needed (allow more content per document)
            text = result['text']
            
            # Add document info with GitHub link
            if github_url:
                doc_info = f"Source: {github_url}\n"
            else:
                doc_info = f"Document: {result['id']}\n"
            
            content = f"{text}\n\n"
            
            # Check if adding this would exceed max_chars
            if current_length + len(doc_info) + len(content) > max_chars:
                break
            
            context_parts.append(doc_info + content)
            current_length += len(doc_info) + len(content)
        
        if not context_parts:
            return "No relevant information found."
        
        return "".join(context_parts).strip()
    
    def get_raw_results_for_ai(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get raw RAG results with GitHub URLs for AI processing.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of dictionaries with 'id', 'text', 'score', and 'github_url' keys
        """
        results = self.search(query, limit)
        
        enhanced_results = []
        for result in results:
            github_url = self._get_github_url(result['id'])
            enhanced_results.append({
                'id': result['id'],
                'text': result['text'],
                'score': result['score'],
                'github_url': github_url
            })
        
        return enhanced_results
    
    def get_detailed_context(self, query: str, max_chars: int = 6000) -> str:
        """
        Get detailed context with more content per document.
        
        Args:
            query: Search query
            max_chars: Maximum characters to include in context
            
        Returns:
            Formatted context string with more detailed content
        """
        results = self.search(query, limit=2)  # Fewer results, more content each
        
        if not results:
            return "No relevant information found."
        
        context_parts = []
        current_length = 0
        
        for result in results:
            # Get GitHub URL for this document
            github_url = self._get_github_url(result['id'])
            
            # Allow much more content per document
            text = result['text']
            
            # Add document info with GitHub link
            if github_url:
                doc_info = f"Source: {github_url}\n"
            else:
                doc_info = f"Document: {result['id']}\n"
            
            content = f"{text}\n\n"
            
            # Check if adding this would exceed max_chars
            if current_length + len(doc_info) + len(content) > max_chars:
                break
            
            context_parts.append(doc_info + content)
            current_length += len(doc_info) + len(content)
        
        if not context_parts:
            return "No relevant information found."
        
        return "".join(context_parts).strip()
    
    def is_available(self) -> bool:
        """Check if the RAG service is available and ready."""
        return self.embeddings is not None


# Global instance for the bot to use
rag_service = None

def get_rag_service() -> Optional[RAGService]:
    """Get the global RAG service instance."""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service 