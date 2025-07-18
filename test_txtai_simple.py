#!/usr/bin/env python3
"""
Simple test to see if txtai can handle raw files directly
"""

import os
from pathlib import Path

try:
    from txtai.embeddings import Embeddings
    TXTAI_AVAILABLE = True
except ImportError:
    print("txtai not available, testing with simple text processing instead")
    TXTAI_AVAILABLE = False

def test_txtai_raw_files():
    """Test if txtai can handle raw files directly"""
    
    if not TXTAI_AVAILABLE:
        print("Testing with simple text processing...")
        test_simple_text_processing()
        return
    
    # Create embeddings instance
    embeddings = Embeddings({"path": "sentence-transformers/all-MiniLM-L6-v2", "content": True})
    
    # Test with actual files from our knowledge base
    test_files = [
        "knowledge_base/raw/microlens_submit/microlens-submit/README.md",
        "knowledge_base/raw/microlens_submit/microlens-submit/validate_submission.py", 
        "knowledge_base/raw/microlens_submit/microlens-submit/agents.md"
    ]
    
    documents = []
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"Reading {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append((file_path, content, None))
                print(f"  - Length: {len(content)} chars")
    
    if documents:
        print(f"\nIndexing {len(documents)} documents...")
        embeddings.index(documents)
        
        print("\nTesting search...")
        results = embeddings.search("function", 3)
        for result in results:
            print(f"  - {result['id']}: {result['text'][:100]}...")
    else:
        print("No test files found")

def test_simple_text_processing():
    """Simple test to show raw file content"""
    
    test_files = [
        "knowledge_base/raw/microlens_submit/microlens-submit/README.md",
        "knowledge_base/raw/microlens_submit/microlens-submit/validate_submission.py", 
        "knowledge_base/raw/microlens_submit/microlens-submit/agents.md"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n=== {file_path} ===")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Length: {len(content)} chars")
                print(f"First 200 chars: {content[:200]}...")
                print(f"Contains 'function': {'function' in content.lower()}")
                print(f"Contains 'class': {'class' in content.lower()}")
                print(f"Contains 'def': {'def' in content.lower()}")
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    test_txtai_raw_files() 