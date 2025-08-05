#!/usr/bin/env python3
"""
Test script for the LLM service.
"""

import os
import sys
from pathlib import Path

# Add the bot directory to the path (now relative to tests/)
sys.path.insert(0, str(Path(__file__).parent.parent / "bot"))

def test_llm_service():
    """Test the LLM service functionality."""
    
    # Set the environment variable for OpenMP
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    # Set Nancy's base directory
    os.environ['NANCY_BASE_DIR'] = str(Path(__file__).parent.parent)
    
    print("=== Testing LLM Service ===\n")
    
    try:
        # Fix import paths for the bot modules
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from bot.plugins.llm.llm_service import LLMService
        from bot.plugins.rag.rag_service import get_rag_service
        
        # Check if RAG service is available first
        rag = get_rag_service()
        if not rag.is_available():
            print("❌ RAG service not available - need RAG for LLM tests")
            return False
        
        print("✅ RAG service available\n")
        
        # Initialize LLM service
        llm = LLMService(debugging=True)
        print("✅ LLM service initialized\n")
        
        # Test 1: Check configuration
        print("=== Test 1: Configuration ===")
        print(f"System prompt path: {llm.system_prompt}")
        print(f"System prompt exists: {llm.system_prompt.exists()}")
        print(f"Max turns: {llm.max_turns}")
        print(f"Model weights path: {llm.model_weights_path}")
        print(f"Model weights exists: {llm.model_weights_path.exists()}")
        print()
        
        # Test 2: RAG integration
        print("=== Test 2: RAG Integration ===")
        test_query = "ping"
        try:
            context = llm.get_initial_context(test_query)
            print(f"✅ get_initial_context works")
            print(f"Context length: {len(context)} chars")
            print(f"Context preview: {context[:200]}...")
        except Exception as e:
            print(f"❌ get_initial_context failed: {e}")
            return False
        print()
        
        # Test 3: Payload construction
        print("=== Test 3: Payload Construction ===")
        try:
            payload = llm.construct_query_payload(test_query, context)
            print(f"✅ construct_query_payload works")
            print(f"Payload keys: {list(payload.keys())}")
            print(f"Contents length: {len(payload.get('contents', []))}")
            
            # Check if system prompt is loaded
            if 'contents' in payload and payload['contents']:
                first_content = payload['contents'][0]
                if 'parts' in first_content and first_content['parts']:
                    system_text = first_content['parts'][0].get('text', '')
                    print(f"System prompt loaded: {len(system_text)} chars")
                    print(f"System prompt preview: {system_text[:100]}...")
                    
        except Exception as e:
            print(f"❌ construct_query_payload failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        print()
        
        # Test 4: Environment variables
        print("=== Test 4: Environment Check ===")
        from dotenv import load_dotenv
        
        # Load from the correct path
        env_path = Path(__file__).parent.parent / "bot/config/.env"
        load_dotenv(env_path)
        
        gemini_key = os.environ.get("GEMINI_API_KEY")
        gemini_model = os.environ.get("GEMINI_MODEL")
        
        print(f"Environment file: {env_path}")
        print(f"Environment file exists: {env_path.exists()}")
        print(f"GEMINI_API_KEY set: {'Yes' if gemini_key else 'No'}")
        if gemini_key:
            print(f"GEMINI_API_KEY length: {len(gemini_key)}")
        print(f"GEMINI_MODEL: {gemini_model}")
        print()
        
        # Test 5: Mock LLM call (without actually calling API)
        print("=== Test 5: Mock LLM Call ===")
        try:
            # Create a mock response to test the parsing
            mock_response = {
                'candidates': [{
                    'content': {
                        'parts': [{
                            'text': '[BEGIN RESPONSE]\nHello! This is a test response.\n[END RESPONSE]'
                        }]
                    }
                }]
            }
            
            # Test response parsing
            llm_text = mock_response['candidates'][0]['content']['parts'][0]['text']
            assistant_response = f"\n\nTURN 1:\n\n{llm_text}\n"
            
            print(f"✅ Response parsing works")
            print(f"LLM text: {llm_text}")
            print(f"Assistant response length: {len(assistant_response)}")
            
            # Test response tool
            from bot.plugins.llm.tools import response_tool
            response_text = response_tool(llm, llm_text)
            print(f"✅ Response tool works")
            print(f"Extracted response: {response_text}")
            
        except Exception as e:
            print(f"❌ Mock LLM call failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        print()
        
        print("✅ All LLM service tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_service()
    sys.exit(0 if success else 1)
