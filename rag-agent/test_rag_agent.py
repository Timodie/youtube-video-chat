#!/usr/bin/env python3

import asyncio
from dotenv import load_dotenv
import os
from supabase import create_client, Client
from openai import AsyncOpenAI

from rag_agent import youtube_ai_assistant, PydanticAIDeps

load_dotenv()

async def test_rag_agent():
    """Test the YouTube RAG agent with sample queries."""

    # Initialize clients
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )

    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Create dependencies
    deps = PydanticAIDeps(
        supabase=supabase,
        openai_client=openai_client
    )

    # Test video ID (from your sample data)
    test_video_id = "dQw4w9WgXcQ"

    print("🤖 YouTube Video RAG Agent Test")
    print("=" * 50)
    print(f"Testing with video ID: {test_video_id}")
    print()

    # Test queries
    test_queries = [
        "What is this video about?",
        "Tell me about love",
        "What happens at the beginning?",
        "Summarize looks like you love you last night the content",
        "Show me the timeline"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"🔍 Test {i}: {query}")
        print("-" * 30)

        try:
            # Run the agent with the query and video_id context
            # Note: You'll need to pass video_id as part of the conversation context
            result = await youtube_ai_assistant.run(
                f"Video ID: {test_video_id}\nUser Question: {query}",
                deps=deps
            )

            print(f"📝 Response:")
            print(result.data)
            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            print()

    print("✅ Test completed!")

async def interactive_mode():
    """Interactive mode for testing the RAG agent."""

    # Initialize clients
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )

    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Create dependencies
    deps = PydanticAIDeps(
        supabase=supabase,
        openai_client=openai_client
    )

    print("🤖 YouTube Video RAG Agent - Interactive Mode")
    print("=" * 50)
    print("Available commands:")
    print("  - Ask questions about the video")
    print("  - Type 'quit' to exit")
    print("  - Type 'video <video_id>' to change video context")
    print()

    current_video_id = "dQw4w9WgXcQ"  # Default test video
    print(f"Current video: {current_video_id}")
    print()

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break

            if user_input.lower().startswith('video '):
                current_video_id = user_input[6:].strip()
                print(f"📺 Switched to video: {current_video_id}")
                continue

            if not user_input:
                continue

            print("🤖 Assistant: ", end="", flush=True)

            # Run the agent
            result = await youtube_ai_assistant.run(
                f"Video ID: {current_video_id}\nUser Question: {user_input}",
                deps=deps
            )

            print(result.data)
            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_rag_agent())
