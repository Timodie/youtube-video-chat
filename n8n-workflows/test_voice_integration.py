#!/usr/bin/env python3
"""
Test script for YouTube Voice Agent + ElevenLabs + Supabase integration
Tests the n8n workflow with real data from your Supabase database
"""

import os
import json
import requests
import asyncio
from supabase import create_client, Client
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv('../rag-agent/.env')

# Configuration
N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/youtube-voice-chat"  # Update this
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def test_supabase_connection():
    """Test connection to Supabase and check for existing data"""
    print("🔍 Testing Supabase connection...")
    
    try:
        # Check youtube_transcript_pages table
        transcript_result = supabase.from_('youtube_transcript_pages').select('video_id, title').limit(5).execute()
        print(f"✅ Found {len(transcript_result.data)} videos with transcript data:")
        
        video_data = []
        for video in transcript_result.data:
            video_id = video['video_id']
            title = video['title']
            
            # Count chunks for this video
            count_result = supabase.from_('youtube_transcript_pages') \
                .select('*', count='exact') \
                .eq('video_id', video_id) \
                .execute()
            
            chunk_count = count_result.count
            video_data.append({
                'video_id': video_id,
                'title': title,
                'chunk_count': chunk_count
            })
            print(f"  - {video_id}: {title} ({chunk_count} chunks)")
        
        # Check chat_histories table exists
        try:
            chat_result = supabase.from_('chat_histories').select('video_id').limit(1).execute()
            print(f"✅ Chat histories table exists with {len(chat_result.data)} records")
        except Exception as e:
            print(f"⚠️ Chat histories table may not exist yet: {e}")
        
        return video_data[0] if video_data else None
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return None

def test_embedding_generation(question: str):
    """Test OpenAI embedding generation"""
    print(f"🔍 Testing embedding generation for: '{question}'")
    
    try:
        response = asyncio.run(_generate_embedding(question))
        print(f"✅ Generated embedding with {len(response)} dimensions")
        return response
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None

async def _generate_embedding(text: str):
    """Generate embedding using OpenAI"""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def test_vector_search(video_id: str, question: str):
    """Test vector search functionality"""
    print(f"🔍 Testing vector search for video {video_id} with question: '{question}'")
    
    try:
        # Generate embedding for the question
        embedding = asyncio.run(_generate_embedding(question))
        
        # Perform vector search
        result = supabase.rpc('match_youtube_transcript_pages', {
            'query_embedding': embedding,
            'match_count': 5,
            'filter': {'video_id': video_id}
        }).execute()
        
        print(f"✅ Vector search returned {len(result.data)} results:")
        for i, chunk in enumerate(result.data[:3]):  # Show top 3
            similarity = chunk.get('similarity', 0)
            content_preview = chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
            print(f"  {i+1}. Similarity: {similarity:.3f} - {content_preview}")
        
        return result.data
        
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return []

def test_webhook_request(video_id: str, question: str, session_id: str = None):
    """Test the n8n webhook endpoint"""
    print(f"🔍 Testing webhook request for video {video_id}...")
    
    payload = {
        "question": question,
        "video_id": video_id,
        "session_id": session_id or f"test-session-{video_id}"
    }
    
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook request successful!")
            print(f"  Response: {result.get('response', '')[:200]}...")
            print(f"  Timestamps: {result.get('timestamps', [])}")
            print(f"  Context chunks used: {result.get('context_chunks', 0)}")
            return result
        else:
            print(f"❌ Webhook request failed with status {response.status_code}")
            print(f"  Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to webhook URL. Make sure:")
        print("  1. n8n workflow is active")
        print("  2. Webhook URL is correct")
        print("  3. n8n instance is accessible")
        return None
    except Exception as e:
        print(f"❌ Webhook request failed: {e}")
        return None

def test_conversation_memory(video_id: str):
    """Test conversation memory by asking follow-up questions"""
    print(f"🔍 Testing conversation memory for video {video_id}...")
    
    session_id = f"memory-test-{video_id}"
    
    # First question
    print("\n--- First Question ---")
    result1 = test_webhook_request(video_id, "What is this video about?", session_id)
    
    if result1 and result1.get('success'):
        print("\n--- Follow-up Question ---")
        # Follow-up question that requires memory
        result2 = test_webhook_request(video_id, "Can you elaborate on that point?", session_id)
        
        if result2 and result2.get('success'):
            print("✅ Conversation memory test successful!")
            return True
    
    print("❌ Conversation memory test failed")
    return False

def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 Starting comprehensive YouTube Voice Agent integration test...\n")
    
    # Test 1: Supabase Connection
    test_video = test_supabase_connection()
    if not test_video:
        print("❌ Cannot continue tests without video data")
        return False
    
    video_id = test_video['video_id']
    print(f"\n📹 Using test video: {video_id} - {test_video['title']}")
    
    # Test 2: Embedding Generation
    test_question = "What is this video about?"
    embedding = test_embedding_generation(test_question)
    if not embedding:
        print("❌ Cannot continue without embedding generation")
        return False
    
    # Test 3: Vector Search
    search_results = test_vector_search(video_id, test_question)
    if not search_results:
        print("❌ Vector search failed")
        return False
    
    # Test 4: Webhook Request
    print(f"\n🌐 Testing n8n webhook...")
    print(f"Webhook URL: {N8N_WEBHOOK_URL}")
    webhook_result = test_webhook_request(video_id, test_question)
    
    # Test 5: Conversation Memory (if webhook works)
    if webhook_result and webhook_result.get('success'):
        print(f"\n🧠 Testing conversation memory...")
        memory_success = test_conversation_memory(video_id)
    
    print(f"\n📊 Test Summary:")
    print(f"✅ Supabase Connection: Working")
    print(f"✅ Embedding Generation: Working") 
    print(f"✅ Vector Search: Working")
    print(f"{'✅' if webhook_result else '❌'} Webhook Request: {'Working' if webhook_result else 'Failed'}")
    
    if webhook_result:
        print(f"{'✅' if 'memory_success' in locals() and memory_success else '❌'} Conversation Memory: {'Working' if 'memory_success' in locals() and memory_success else 'Failed'}")
    
    return bool(webhook_result)

if __name__ == "__main__":
    print("YouTube Voice Agent Integration Test")
    print("=" * 50)
    
    # Check environment variables
    if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
        print("❌ Missing required environment variables:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_KEY") 
        print("  - OPENAI_API_KEY")
        exit(1)
    
    if N8N_WEBHOOK_URL == "https://your-n8n-instance.com/webhook/youtube-voice-chat":
        print("⚠️ Please update N8N_WEBHOOK_URL in the script with your actual n8n webhook URL")
        print("You can still run database tests...")
        print()
    
    # Run tests
    success = run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! Your integration is ready for ElevenLabs.")
        print("\nNext steps:")
        print("1. Configure your ElevenLabs voice agent with the webhook URL")
        print("2. Test voice conversations using the ElevenLabs interface")
        print("3. Monitor usage and costs in production")
    else:
        print("\n❌ Some tests failed. Check the errors above and:")
        print("1. Verify your n8n workflow is active and accessible")
        print("2. Check all credentials are configured correctly")
        print("3. Ensure your Supabase database has transcript data")