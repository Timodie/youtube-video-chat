import sys
import os
import asyncio
from typing import Optional, Dict, Any, List
import traceback
from datetime import datetime

# Add rag-agent to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag-agent'))

try:
    from rag_agent import youtube_ai_assistant, PydanticAIDeps
    from ingest_youtube import process_and_store_transcript
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ RAG components not available: {e}")
    RAG_AVAILABLE = False

class RAGIntegration:
    """Integration layer between Flask server and RAG agent."""
    
    def __init__(self, supabase_client, openai_client):
        if not RAG_AVAILABLE:
            raise Exception("RAG dependencies not available. Check rag-agent installation.")
        
        self.deps = PydanticAIDeps(
            supabase=supabase_client,
            openai_client=openai_client
        )
        print("✅ RAG Integration initialized")
    
    async def ingest_transcript(
        self, 
        video_id: str, 
        video_url: str, 
        video_title: str, 
        transcript_data: List[Dict]
    ) -> bool:
        """
        Safely ingest transcript data into RAG system.
        
        Args:
            video_id: YouTube video ID
            video_url: Full YouTube URL
            video_title: Video title
            transcript_data: Parsed VTT transcript data
            
        Returns:
            bool: True if ingestion succeeded, False otherwise
        """
        try:
            print(f"🔄 Starting RAG ingest for video {video_id}")
            print(f"   Title: {video_title}")
            print(f"   Transcript entries: {len(transcript_data)}")
            
            # Call the ingest function from rag-agent
            result = await process_and_store_transcript(
                video_id=video_id,
                video_url=video_url,
                video_title=video_title,
                transcript_data=transcript_data
            )
            
            if result:
                print(f"✅ RAG ingest completed successfully for video {video_id}")
                print(f"   Stored {len(result)} chunks in database")
                return True
            else:
                print(f"⚠️ RAG ingest returned no results for video {video_id}")
                return False
                
        except Exception as e:
            print(f"❌ RAG ingest failed for video {video_id}")
            print(f"   Error: {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
            return False
    
    async def chat_with_video(self, video_id: str, chat_input: str) -> Dict[str, Any]:
        """
        Chat with RAG agent about video content.
        
        Args:
            video_id: YouTube video ID for context
            chat_input: User's question/message
            
        Returns:
            Dict with response, success status, and optional timestamps
        """
        try:
            print(f"💬 Processing chat for video {video_id}")
            print(f"   Query: {chat_input}")
            
            # Prepare the prompt with video context
            prompt = f"Video ID: {video_id}\nUser Question: {chat_input}"
            
            # Run the RAG agent
            result = await youtube_ai_assistant.run(prompt, deps=self.deps)
            
            print(f"✅ RAG agent response generated")
            print(f"   Response length: {len(str(result.data))} characters")
            
            # Extract response and any timestamps/metadata
            response_text = str(result.data)
            
            # Try to extract timestamps from response for video navigation
            import re
            timestamps = re.findall(r'\[(\d{2}:\d{2}:\d{2}|\d{2}:\d{2})\]', response_text)
            
            return {
                "success": True,
                "response": response_text,
                "timestamps": timestamps,
                "video_id": video_id,
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ RAG chat failed for video {video_id}")
            print(f"   Error: {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
            
            return {
                "success": False,
                "response": "I'm sorry, I couldn't process your question about this video. Please try again or ensure the video transcript has been processed.",
                "error": str(e),
                "timestamps": [],
                "video_id": video_id,
                "processed_at": datetime.utcnow().isoformat()
            }
    
    async def check_video_availability(self, video_id: str) -> Dict[str, Any]:
        """
        Check if a video's transcript data is available in the RAG system.
        
        Args:
            video_id: YouTube video ID to check
            
        Returns:
            Dict with availability status and metadata
        """
        try:
            # Query database for video chunks
            result = self.deps.supabase.from_('youtube_transcript_pages') \
                .select('chunk_number', count='exact') \
                .eq('video_id', video_id) \
                .execute()
            
            chunk_count = result.count if result.count else 0
            
            return {
                "available": chunk_count > 0,
                "chunk_count": chunk_count,
                "video_id": video_id
            }
            
        except Exception as e:
            print(f"❌ Error checking video availability: {e}")
            return {
                "available": False,
                "chunk_count": 0,
                "video_id": video_id,
                "error": str(e)
            }

def create_rag_integration(supabase_client, openai_client) -> Optional[RAGIntegration]:
    """
    Factory function to create RAG integration with proper error handling.
    
    Returns:
        RAGIntegration instance or None if creation fails
    """
    try:
        return RAGIntegration(supabase_client, openai_client)
    except Exception as e:
        print(f"❌ Failed to create RAG integration: {e}")
        return None