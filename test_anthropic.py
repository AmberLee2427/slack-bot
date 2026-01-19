import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ Error: ANTHROPIC_API_KEY not found in environment or bot/config/.env")
    exit(1)

print(f"✅ Found API Key: {api_key[:15]}...{api_key[-4:]}")

client = Anthropic(api_key=api_key)

print(f"🔍 Client Base URL: {client.base_url}")

models_to_test = [
    "claude-sonnet-4-5-20250929",
    "claude-opus-4-5-20251101"
]

print("\n🚀 Testing Anthropic API connectivity...\n")

for model in models_to_test:
    print(f"Testing model: {model}...")
    try:
        message = client.messages.create(
            model=model,
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Hello, are you working?"}
            ]
        )
        print(f"✅ Success! Response: {message.content[0].text.strip()}")
    except Exception as e:
        print(f"❌ Failed: {type(e).__name__}: {e}")
    print("-" * 50)
