#!/usr/bin/env python3
"""
Test script for the RAG service.
"""

import os
import sys
from pathlib import Path

# Add the bot directory to the path (now relative to tests/)
sys.path.insert(0, str(Path(__file__).parent.parent / "bot"))

def test_rag_service():
    """Test the RAG service functionality."""
    
    # Set the environment variable for OpenMP
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    print("=== Testing RAG Service ===\n")
    
    try:
        from rag_service import get_rag_service
        
        # Get the RAG service
        rag = get_rag_service()
        
        if not rag.is_available():
            print("❌ RAG service not available")
            print("Make sure to run the knowledge base build first:")
            print("python scripts/build_knowledge_base.py --category microlens_submit --dirty")
            return False
        
        print("✅ RAG service loaded successfully\n")
        
        # Test queries
        test_queries = [
            "submission validation",
            "submission dossier",
            "parameter validation",
            "CLI commands"
        ]
        
        for query in test_queries:
            print(f"Query: '{query}'")
            
            # Test search
            results = rag.search(query, limit=5)
            print(f"  Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"    {i}. {result['id']} (score: {result['score']:.3f})")
                print(f"       {result['text'][:2000]}...")
            
            # Test context
            context = rag.get_context_for_query(query)
            print(f"  Context length: {len(context)} chars")
            print(f"  Context preview: {context[:2000]}...")
            
            # Test AI-ready results
            ai_results = rag.get_raw_results_for_ai(query, limit=1)
            if ai_results:
                print(f"  AI-ready result:")
                print(f"    GitHub URL: {ai_results[0].get('github_url', 'N/A')}")
                print(f"    Content length: {len(ai_results[0]['text'])} chars")
            
            print()
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_service()
    sys.exit(0 if success else 1) 