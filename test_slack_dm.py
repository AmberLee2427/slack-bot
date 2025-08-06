#!/usr/bin/env python3
"""
Test script to debug Slack DM issues with Nancy
"""
import os
import asyncio
import json
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="bot/config/.env")

async def test_slack_api():
    """Test Nancy's Slack API capabilities"""
    token = os.getenv("SLACK_BOT_TOKEN")
    user_id = "U096QG01RED"  # Your user ID
    
    if not token:
        print("❌ No SLACK_BOT_TOKEN found in environment")
        return
        
    print("🔍 Testing Slack API Capabilities...")
    print(f"🎯 Target User: {user_id}")
    print(f"🔑 Token starts with: {token[:12]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Test auth.test
            print("\n1️⃣ Testing bot identity...")
            async with session.post("https://slack.com/api/auth.test", headers=headers) as response:
                auth_data = await response.json()
                if auth_data.get("ok"):
                    print(f"   ✅ Bot User ID: {auth_data['user_id']}")
                    print(f"   ✅ Bot Name: {auth_data['user']}")
                    print(f"   ✅ Team: {auth_data['team']}")
                else:
                    print(f"   ❌ Auth failed: {auth_data.get('error', 'Unknown error')}")
                    return

            # 2. Test conversations.open
            print("\n2️⃣ Testing DM channel creation...")
            dm_payload = {"users": user_id}
            async with session.post("https://slack.com/api/conversations.open", 
                                  headers=headers, json=dm_payload) as response:
                dm_data = await response.json()
                if dm_data.get("ok"):
                    dm_channel = dm_data['channel']['id']
                    print(f"   ✅ DM Channel ID: {dm_channel}")
                    print(f"   ✅ Channel Info: {json.dumps(dm_data['channel'], indent=2)}")
                else:
                    print(f"   ❌ DM creation failed: {dm_data.get('error', 'Unknown error')}")
                    print(f"   📝 Full response: {dm_data}")
                    return

            # 3. Test conversations.info
            print("\n3️⃣ Testing channel info...")
            info_payload = {"channel": dm_channel}
            async with session.post("https://slack.com/api/conversations.info", 
                                  headers=headers, json=info_payload) as response:
                info_data = await response.json()
                if info_data.get("ok"):
                    channel_info = info_data['channel']
                    print(f"   ✅ Is IM: {channel_info.get('is_im', 'Unknown')}")
                    print(f"   ✅ Is Open: {channel_info.get('is_open', 'Unknown')}")
                    print(f"   ✅ User: {channel_info.get('user', 'Unknown')}")
                else:
                    print(f"   ❌ Channel info failed: {info_data.get('error', 'Unknown error')}")

            # 4. Test sending a message
            print("\n4️⃣ Testing message sending...")
            message_payload = {
                "channel": dm_channel,
                "text": "🤖 Hello! This is a test message from Nancy to debug DM issues.",
                "as_user": True
            }
            async with session.post("https://slack.com/api/chat.postMessage", 
                                  headers=headers, json=message_payload) as response:
                message_data = await response.json()
                if message_data.get("ok"):
                    print(f"   ✅ Message sent! Timestamp: {message_data['ts']}")
                else:
                    print(f"   ❌ Message failed: {message_data.get('error', 'Unknown error')}")
                    print(f"   📝 Full response: {message_data}")

            # 5. Test getting conversation history
            print("\n5️⃣ Testing conversation history...")
            history_payload = {"channel": dm_channel, "limit": 5}
            async with session.post("https://slack.com/api/conversations.history", 
                                  headers=headers, json=history_payload) as response:
                history_data = await response.json()
                if history_data.get("ok"):
                    print(f"   ✅ Found {len(history_data['messages'])} recent messages")
                    for i, msg in enumerate(history_data['messages'][:3]):
                        print(f"     � Message {i+1}: {msg.get('text', 'No text')[:50]}...")
                else:
                    print(f"   ❌ History failed: {history_data.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Connection Error: {str(e)}")

async def main():
    print("🚀 Starting Slack DM Debug Session...")
    print("=" * 50)
    
    await test_slack_api()
    
    print("\n" + "=" * 50)
    print("✅ Debug session complete!")

if __name__ == "__main__":
    asyncio.run(main())
