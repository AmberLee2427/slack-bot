#!/usr/bin/env python3
"""
Simple test script to verify txtai retrieval works.
"""

import os
import sys
from pathlib import Path
import traceback

# Add the bot directory to the path (now relative to tests/)
sys.path.insert(0, str(Path(__file__).parent.parent / "bot"))

def test_txtai_import():
    """Test if txtai can be imported"""
    print("Testing txtai import...")
    
    try:
        print("Attempting to import txtai.embeddings...")
        from txtai.embeddings import Embeddings
        print("✅ txtai.embeddings import successful!")
        return True
    except Exception as e:
        print(f"❌ txtai.embeddings import failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

def test_simple_embeddings():
    """Test basic embeddings functionality"""
    print("\nTesting basic embeddings functionality...")
    
    try:
        from txtai.embeddings import Embeddings
        
        # Create a simple embeddings instance
        embeddings = Embeddings({
            "path": "sentence-transformers/all-MiniLM-L6-v2",
            "content": True
        })
        
        # Test with simple data
        documents = [
            ("doc1", "This is a test document about microlensing", None),
            ("doc2", "Another document about gravitational lensing", None),
            ("doc3", "A third document about astronomy", None)
        ]
        
        print("Indexing test documents...")
        embeddings.index(documents)
        
        print("Testing search...")
        results = embeddings.search("microlensing", 2)
        
        print("Search results:")
        for result in results:
            print(f"  - {result['id']}: {result['text']}")
        
        print("✅ Basic embeddings functionality works!")
        return True
        
    except Exception as e:
        print(f"❌ Basic embeddings test failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== txtai Import Test ===\n")
    
    if test_txtai_import():
        test_simple_embeddings()
    else:
        print("\n❌ Cannot proceed without txtai import")
        print("\nTroubleshooting suggestions:")
        print("1. Try: pip install --upgrade transformers")
        print("2. Try: pip install --upgrade txtai")
        print("3. Check if there are conflicting local installations") 