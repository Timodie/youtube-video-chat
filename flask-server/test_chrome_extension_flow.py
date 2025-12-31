#!/usr/bin/env python3
"""
Test script that simulates Chrome extension behavior with the Flask server.
Tests the complete flow: transcript extraction → RAG ingest → chat interaction
"""

import requests
import json
import time
import asyncio
from typing import Dict, Any, List

# Test configuration
BASE_URL = "http://localhost:5001"
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
TEST_VIDEO_ID = "dQw4w9WgXcQ"

class ChromeExtensionSimulator:
    """Simulates Chrome extension interactions with Flask server."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Chrome Extension Test'
        })

    def test_health(self) -> bool:
        """Test if Flask server is running."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Flask server is healthy")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Could not connect to Flask server: {e}")
            return False

    def extract_transcript(self, video_url: str) -> Dict[str, Any]:
        """
        Simulate Chrome extension requesting transcript extraction.
        This is what happens when user clicks the transcript button.
        """
        print(f"\n🎬 STEP 1: Extract Transcript")
        print(f"   Video URL: {video_url}")
        print(f"   Simulating: User clicks transcript button in Chrome extension")

        payload = {"url": video_url}

        try:
            print(f"📤 POST {self.base_url}/transcript")
            start_time = time.time()

            response = self.session.post(
                f"{self.base_url}/transcript",
                json=payload,
                timeout=60  # Transcript extraction can take time
            )

            duration = time.time() - start_time
            print(f"⏱️  Request took {duration:.2f} seconds")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Transcript extracted successfully")
                print(f"   Video ID: {data.get('video_id')}")
                print(f"   Title: {data.get('title')}")
                print(f"   Language: {data.get('language')}")
                print(f"   Transcript entries: {len(data.get('transcript', []))}")
                print(f"   RAG stored: {data.get('rag_stored', False)}")
                print(f"   n8n stored: {data.get('n8n_stored', False)}")
                return data
            else:
                print(f"❌ Transcript extraction failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"❌ Request failed: {e}")
            return {"success": False, "error": str(e)}

    def chat_with_video(self, video_id: str, message: str) -> Dict[str, Any]:
        """
        Simulate Chrome extension sending chat message.
        This is what happens when user types in the chat interface.
        """
        print(f"\n💬 CHAT: {message}")
        print(f"   Video ID: {video_id}")
        print(f"   Simulating: User types message in chat interface")

        payload = {
            "chatInput": message,
            "video_id": video_id,
            "sessionId": video_id  # Use video_id as session
        }

        try:
            print(f"📤 POST {self.base_url}/chat")
            start_time = time.time()

            response = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=30
            )

            duration = time.time() - start_time
            print(f"⏱️  Request took {duration:.2f} seconds")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Chat response received")
                print(f"   Method: {data.get('method', 'unknown')}")
                print(f"   Timestamps found: {len(data.get('timestamps', []))}")
                print(f"   Response preview: {str(data.get('response', ''))[:100]}...")
                return data
            else:
                print(f"❌ Chat failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"❌ Chat request failed: {e}")
            return {"success": False, "error": str(e)}

    def simulate_user_journey(self, video_url: str) -> bool:
        """
        Simulate complete user journey:
        1. User opens YouTube video
        2. Clicks transcript button
        3. Asks questions in chat
        """
        print("🚀 SIMULATING CHROME EXTENSION USER JOURNEY")
        print("=" * 60)

        # Step 1: Extract transcript (happens when user clicks transcript button)
        transcript_result = self.extract_transcript(video_url)

        if not transcript_result.get("success", False):
            print("❌ Journey failed at transcript extraction")
            return False

        video_id = transcript_result.get("video_id")
        if not video_id:
            print("❌ No video ID returned")
            return False

        # Wait a moment for processing to complete
        print("\n⏳ Waiting for processing to complete...")
        time.sleep(2)

        # Step 2: Simulate chat interactions (what user would do in chat tab)
        test_messages = [
            "What is this video about?",
            "Tell me about love",
            "What happens at the beginning?",
            "Show me the timeline",
            "Summarize the content"
        ]

        print(f"\n🎯 STEP 2: Chat Interactions")
        print(f"   Simulating: User switches to chat tab and asks questions")

        success_count = 0

        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Chat {i}/{len(test_messages)} ---")

            chat_result = self.chat_with_video(video_id, message)

            if chat_result.get("success", False):
                success_count += 1

                # Display response (like Chrome extension would)
                response = chat_result.get("response", "")
                timestamps = chat_result.get("timestamps", [])

                print(f"🤖 Assistant Response:")
                print(f"   {response[:200]}{'...' if len(response) > 200 else ''}")

                if timestamps:
                    print(f"   🕐 Clickable timestamps: {timestamps[:3]}{'...' if len(timestamps) > 3 else ''}")
            else:
                print(f"❌ Chat {i} failed")

            # Small delay between messages (realistic user behavior)
            time.sleep(1)

        # Summary
        print(f"\n📊 JOURNEY SUMMARY")
        print(f"   Transcript extraction: {'✅' if transcript_result.get('success') else '❌'}")
        print(f"   RAG storage: {'✅' if transcript_result.get('rag_stored') else '❌'}")
        print(f"   Chat success rate: {success_count}/{len(test_messages)} ({success_count/len(test_messages)*100:.0f}%)")

        journey_success = (
            transcript_result.get("success", False) and
            transcript_result.get("rag_stored", False) and
            success_count > 0
        )

        print(f"   Overall journey: {'✅ SUCCESS' if journey_success else '❌ FAILED'}")

        return journey_success

def run_integration_tests():
    """Run comprehensive integration tests."""
    print("🧪 FLASK SERVER + RAG INTEGRATION TESTS")
    print("=" * 60)

    simulator = ChromeExtensionSimulator()

    # Test 1: Health check
    if not simulator.test_health():
        print("❌ Cannot proceed - Flask server not available")
        print("💡 Make sure to run: python app.py")
        return False

    # Test 2: Complete user journey
    print(f"\n🎭 TEST: Complete User Journey")
    success = simulator.simulate_user_journey(TEST_VIDEO_URL)

    if success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   ✅ Your Flask server + RAG integration is working!")
        print(f"   ✅ Chrome extension can safely use these endpoints")
        print(f"   ✅ End-to-end pipeline: transcript → ingest → chat ✅")
    else:
        print(f"\n💥 TESTS FAILED!")
        print(f"   Check the Flask server logs for detailed error information")

    return success

def run_stress_test():
    """Run stress test with multiple concurrent requests."""
    print("\n🔥 STRESS TEST: Multiple Concurrent Chats")
    print("-" * 40)

    simulator = ChromeExtensionSimulator()

    # Assume transcript already extracted
    video_id = TEST_VIDEO_ID
    messages = [
        "What's the main theme?",
        "Tell me more about the lyrics",
        "What genre is this?",
        "Who is the artist?",
        "When was this released?"
    ]

    import concurrent.futures

    def send_chat(message):
        return simulator.chat_with_video(video_id, message)

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(send_chat, msg) for msg in messages]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    duration = time.time() - start_time
    success_count = sum(1 for r in results if r.get("success", False))

    print(f"⚡ Stress test completed in {duration:.2f} seconds")
    print(f"   Success rate: {success_count}/{len(messages)} ({success_count/len(messages)*100:.0f}%)")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "stress":
        run_stress_test()
    else:
        run_integration_tests()

        # Optionally run stress test
        user_input = input("\n🔥 Run stress test? (y/n): ").lower().strip()
        if user_input == 'y':
            run_stress_test()
