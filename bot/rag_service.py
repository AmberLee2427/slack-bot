"""
RAG (Retrieval-Augmented Generation) service for the Slack bot.
Provides semantic search capabilities using txtai embeddings.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class RAGService:
    """Service for retrieving relevant context from the knowledge base."""
    
    def __init__(self, embeddings_path: str = "knowledge_base/embeddings/index"):
        """
        Initialize the RAG service.
        
        Args:
            embeddings_path: Path to the txtai embeddings index
        """
        # Make path relative to project root (bot/ directory parent)
        project_root = Path(__file__).parent.parent
        self.embeddings_path = project_root / embeddings_path
        self.embeddings = None
        self._load_embeddings()
    
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
            results = self.embeddings.search(query, limit)
            
            # Convert to list of dicts for easier handling
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result['id'],
                    'text': result['text'],
                    'score': result.get('score', 0.0)
                })
            
            logger.info(f"Found {len(formatted_results)} results for query: '{query}'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_context_for_query(self, query: str, max_chars: int = 2000) -> str:
        """
        Get formatted context for a query, suitable for LLM prompts.
        
        Args:
            query: Search query
            max_chars: Maximum characters to include in context
            
        Returns:
            Formatted context string
        """
        results = self.search(query, limit=3)
        
        if not results:
            return "No relevant information found."
        
        context_parts = []
        current_length = 0
        
        for result in results:
            # Truncate text if needed
            text = result['text']
            if len(text) > 500:  # Limit individual document length
                text = text[:500] + "..."
            
            # Add document info
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