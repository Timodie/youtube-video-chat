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
        Safely ingest transcript data into RAG system with duplicate detection.
        
        Args:
            video_id: YouTube video ID
            video_url: Full YouTube URL
            video_title: Video title
            transcript_data: Parsed VTT transcript data
            
        Returns:
            bool: True if RAG data is available (new or existing), False if failed
        """
        try:
            print(f"🔄 Starting RAG ingest for video {video_id}")
            print(f"   Title: {video_title}")
            print(f"   Transcript entries: {len(transcript_data)}")
            
            # Check if chunks already exist (duplicate detection)
            existing_chunks = self.deps.supabase.from_('youtube_transcript_pages') \
                .select('chunk_number', count='exact') \
                .eq('video_id', video_id) \
                .execute()
            
            if existing_chunks.count and existing_chunks.count > 0:
                print(f"✅ Video {video_id} already processed with {existing_chunks.count} chunks")
                print(f"   Skipping chunking and embedding generation (cost savings)")
                return True  # RAG data is available for chat
            
            print(f"🆕 No existing chunks found, processing video {video_id}")
            
            # Call the ingest function from rag-agent (only if no chunks exist)
            result = await process_and_store_transcript(
                video_id=video_id,
                video_url=video_url,
                video_title=video_title,
                transcript_data=transcript_data
            )
            
            if result:
                print(f"✅ RAG ingest completed successfully for video {video_id}")
                print(f"   Stored {len(result)} new chunks in database")
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
    
    # =============================================================================
    # CHAT MEMORY HELPER METHODS (Dependency Order Implementation)
    # =============================================================================
    
    # 1. FOUNDATIONAL STORAGE METHODS
    
    async def _store_chat_message(self, video_id: str, session_id: str, role: str, message: str, **kwargs) -> str:
        """
        Store a single message (user, assistant, or summary) in chat history.
        
        Args:
            video_id: YouTube video ID
            session_id: Session identifier (usually same as video_id)
            role: 'user', 'assistant', or 'summary'
            message: The message content
            **kwargs: Optional fields for summaries (summarizes_from_id, summarizes_to_id)
            
        Returns:
            str: The UUID of the stored message
        """
        try:
            data = {
                "video_id": video_id,
                "session_id": session_id,
                "role": role,
                "message": message
            }
            
            # Add summary-specific fields if provided
            if kwargs.get('summarizes_from_id'):
                data['summarizes_from_id'] = kwargs['summarizes_from_id']
            if kwargs.get('summarizes_to_id'):
                data['summarizes_to_id'] = kwargs['summarizes_to_id']
            
            result = self.deps.supabase.from_('chat_histories').insert(data).execute()
            
            if result.data and len(result.data) > 0:
                message_id = result.data[0]['id']
                print(f"💾 Stored {role} message for video {video_id}: {message_id}")
                return message_id
            else:
                print(f"⚠️ Failed to store {role} message for video {video_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error storing {role} message for video {video_id}: {e}")
            return None
    
    async def _store_summary_message(self, video_id: str, session_id: str, summary_text: str, from_id: str, to_id: str) -> str:
        """
        Store a conversation summary with range tracking.
        
        Args:
            video_id: YouTube video ID
            session_id: Session identifier
            summary_text: The generated summary content
            from_id: UUID of first message being summarized
            to_id: UUID of last message being summarized
            
        Returns:
            str: UUID of stored summary or None if failed
        """
        return await self._store_chat_message(
            video_id, session_id, 
            role="summary", 
            message=summary_text,
            summarizes_from_id=from_id,
            summarizes_to_id=to_id
        )
    
    # 2. BASIC RETRIEVAL METHODS
    
    async def _get_all_messages(self, video_id: str, session_id: str) -> List[Dict]:
        """
        Get all user/assistant messages for UI display (excludes summaries).
        
        Args:
            video_id: YouTube video ID
            session_id: Session identifier
            
        Returns:
            List[Dict]: Messages ordered by timestamp, suitable for UI display
        """
        try:
            result = self.deps.supabase.from_('chat_histories') \
                .select('id, role, message, timestamp') \
                .eq('video_id', video_id) \
                .eq('session_id', session_id) \
                .in_('role', ['user', 'assistant']) \
                .order('timestamp') \
                .execute()
            
            messages = result.data if result.data else []
            print(f"📄 Retrieved {len(messages)} display messages for video {video_id}")
            return messages
            
        except Exception as e:
            print(f"❌ Error retrieving messages for video {video_id}: {e}")
            return []
    
    async def _get_recent_messages(self, video_id: str, session_id: str, limit: int = 8) -> List[Dict]:
        """
        Get last N user/assistant messages for LLM context.
        
        Args:
            video_id: YouTube video ID
            session_id: Session identifier
            limit: Number of recent messages to retrieve (default 8 = 4 exchanges)
            
        Returns:
            List[Dict]: Recent messages ordered by timestamp
        """
        try:
            result = self.deps.supabase.from_('chat_histories') \
                .select('id, role, message, timestamp') \
                .eq('video_id', video_id) \
                .eq('session_id', session_id) \
                .in_('role', ['user', 'assistant']) \
                .order('timestamp', desc=True) \
                .limit(limit) \
                .execute()
            
            # Reverse to get chronological order (oldest first)
            messages = list(reversed(result.data)) if result.data else []
            print(f"🔄 Retrieved {len(messages)} recent messages for video {video_id}")
            return messages
            
        except Exception as e:
            print(f"❌ Error retrieving recent messages for video {video_id}: {e}")
            return []
    
    async def _count_messages(self, video_id: str, session_id: str) -> int:
        """
        Count total user/assistant messages in conversation.
        
        Args:
            video_id: YouTube video ID
            session_id: Session identifier
            
        Returns:
            int: Total count of user/assistant messages
        """
        try:
            result = self.deps.supabase.from_('chat_histories') \
                .select('id', count='exact') \
                .eq('video_id', video_id) \
                .eq('session_id', session_id) \
                .in_('role', ['user', 'assistant']) \
                .execute()
            
            count = result.count if result.count else 0
            print(f"📊 Conversation has {count} messages for video {video_id}")
            return count
            
        except Exception as e:
            print(f"❌ Error counting messages for video {video_id}: {e}")
            return 0
    
    # 3. SUMMARY MANAGEMENT METHODS
    
    async def _find_summary_covering_range(self, video_id: str, session_id: str, from_id: str, to_id: str) -> Optional[Dict]:
        """
        Check if existing summary covers the specified message range.
        
        Args:
            video_id: YouTube video ID
            session_id: Session identifier
            from_id: UUID of first message in range
            to_id: UUID of last message in range
            
        Returns:
            Dict with summary data or None if not found
        """
        try:
            result = self.deps.supabase.from_('chat_histories') \
                .select('id, message, timestamp') \
                .eq('video_id', video_id) \
                .eq('session_id', session_id) \
                .eq('role', 'summary') \
                .eq('summarizes_from_id', from_id) \
                .eq('summarizes_to_id', to_id) \
                .single() \
                .execute()
            
            if result.data:
                print(f"✅ Found existing summary for range {from_id[:8]}...{to_id[:8]} in video {video_id}")
                return result.data
            else:
                print(f"🔍 No existing summary found for range {from_id[:8]}...{to_id[:8]} in video {video_id}")
                return None
                
        except Exception as e:
            print(f"❌ Error finding summary for video {video_id}: {e}")
            return None
    
    async def _generate_conversation_summary(self, messages: List[Dict]) -> str:
        """
        Generate summary of conversation segment using OpenAI.
        
        Args:
            messages: List of message dictionaries to summarize
            
        Returns:
            str: Generated summary text
        """
        try:
            # Format messages for summarization
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['message']}" 
                for msg in messages
            ])
            
            print(f"🤖 Generating summary for {len(messages)} messages (~{len(conversation_text)} chars)")
            
            # Generate summary using OpenAI
            response = await self.deps.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective model for summarization
                messages=[{
                    "role": "system",
                    "content": "Summarize this conversation about a YouTube video in 2-3 sentences. Focus on key topics discussed and questions asked. Be concise but capture the main points."
                }, {
                    "role": "user", 
                    "content": conversation_text
                }],
                max_tokens=150,  # Keep summaries concise
                temperature=0.3  # Lower temperature for consistent summaries
            )
            
            summary = response.choices[0].message.content.strip()
            print(f"✅ Generated summary: {summary[:100]}...")
            return summary
            
        except Exception as e:
            print(f"❌ Error generating conversation summary: {e}")
            return f"Summary of {len(messages)} messages about the video content."
    
    async def _get_or_create_summary(self, video_id: str, session_id: str, messages_to_summarize: List[Dict]) -> str:
        """
        Get existing summary for message range or create new one.
        
        Args:
            video_id: YouTube video ID
            session_id: Session identifier
            messages_to_summarize: List of messages that need summarizing
            
        Returns:
            str: Summary text (existing or newly generated)
        """
        if not messages_to_summarize:
            return "No previous conversation to summarize."
        
        try:
            from_id = messages_to_summarize[0]['id']
            to_id = messages_to_summarize[-1]['id']
            
            # Check if we already have a summary for this range
            existing_summary = await self._find_summary_covering_range(
                video_id, session_id, from_id, to_id
            )
            
            if existing_summary:
                print(f"♻️ Using existing summary for video {video_id}")
                return existing_summary['message']
            
            # Generate new summary (costs ~$0.01-0.05, done once)
            print(f"🆕 Creating new summary for {len(messages_to_summarize)} messages in video {video_id}")
            summary_text = await self._generate_conversation_summary(messages_to_summarize)
            
            # Store summary with range metadata
            summary_id = await self._store_summary_message(
                video_id, session_id, summary_text, from_id, to_id
            )
            
            if summary_id:
                print(f"💾 Stored new summary {summary_id} for video {video_id}")
            else:
                print(f"⚠️ Failed to store summary for video {video_id}")
            
            return summary_text
            
        except Exception as e:
            print(f"❌ Error in get_or_create_summary for video {video_id}: {e}")
            return f"Summary of conversation about video {video_id}."
    
    # 4. CONTEXT BUILDING METHODS (Main orchestration)
    
    async def _format_messages_for_llm(self, video_id: str, messages: List[Dict]) -> str:
        """
        Format messages into LLM prompt string.
        
        Args:
            video_id: YouTube video ID for context
            messages: List of message dictionaries
            
        Returns:
            str: Formatted prompt for LLM
        """
        formatted_messages = []
        
        for msg in messages:
            formatted_messages.append(f"{msg['role']}: {msg['message']}")
        
        conversation_text = "\n".join(formatted_messages)
        
        prompt = f"""Video ID: {video_id}

Recent conversation:
{conversation_text}

Current question: {messages[-1]['message'] if messages else ""}"""
        
        return prompt
    
    async def _format_recent_messages(self, messages: List[Dict]) -> str:
        """
        Format recent messages for LLM context.
        
        Args:
            messages: List of recent message dictionaries
            
        Returns:
            str: Formatted recent conversation
        """
        if not messages:
            return "No recent conversation."
        
        formatted = []
        for msg in messages:
            formatted.append(f"{msg['role']}: {msg['message']}")
        
        return "\n".join(formatted)
    
    async def _build_llm_context(self, video_id: str, session_id: str) -> Dict:
        """
        Main method: builds dual context for LLM efficiency + UI display.
        
        This is the core orchestration method that implements our dual-context strategy:
        - Full conversation history for UI display 
        - Efficient context (summary + recent) for LLM processing
        
        Args:
            video_id: YouTube video ID
            session_id: Session identifier
            
        Returns:
            Dict: {
                "llm_prompt": str,           # Efficient context for LLM
                "display_messages": List[Dict]  # Full history for UI
            }
        """
        try:
            print(f"🔄 Building dual context for video {video_id}")
            
            # Get ALL user/assistant messages for UI display
            all_messages = await self._get_all_messages(video_id, session_id)
            print(f"📱 UI will display {len(all_messages)} total messages")
            
            # Short conversation - send everything to LLM (no summarization needed)
            if len(all_messages) <= 12:
                print(f"📝 Short conversation ({len(all_messages)} messages) - sending all to LLM")
                llm_prompt = self._format_messages_for_llm(video_id, all_messages)
                
                return {
                    "llm_prompt": llm_prompt,
                    "display_messages": all_messages
                }
            
            # Long conversation - use summary + recent for LLM efficiency
            print(f"📚 Long conversation ({len(all_messages)} messages) - using summary + recent")
            
            recent_messages = all_messages[-8:]  # Last 4 exchanges for immediate context
            older_messages = all_messages[:-8]   # Everything else gets summarized
            
            print(f"   Recent: {len(recent_messages)} messages")
            print(f"   Older: {len(older_messages)} messages (will summarize)")
            
            # Get or create summary for older messages
            summary = await self._get_or_create_summary(video_id, session_id, older_messages)
            
            # Build efficient LLM context with summary + recent
            recent_formatted = await self._format_recent_messages(recent_messages)
            
            llm_prompt = f"""Video ID: {video_id}

Previous conversation summary: {summary}

Recent conversation:
{recent_formatted}

Current question: {recent_messages[-1]['message'] if recent_messages else ""}"""
            
            print(f"✅ Built efficient LLM context (~{len(llm_prompt)} chars) for {len(all_messages)} total messages")
            
            return {
                "llm_prompt": llm_prompt,
                "display_messages": all_messages  # Full history for frontend
            }
            
        except Exception as e:
            print(f"❌ Error building LLM context for video {video_id}: {e}")
            
            # Fallback: return basic context
            return {
                "llm_prompt": f"Video ID: {video_id}\n\nCurrent question: Unable to load conversation history.",
                "display_messages": []
            }
    
    # 5. OPTIONAL CLEANUP AND UTILITY METHODS
    
    async def _cleanup_old_sessions(self, days_old: int = 7) -> Dict:
        """
        Remove chat histories older than specified days.
        
        Args:
            days_old: Number of days after which to remove chat histories
            
        Returns:
            Dict: Cleanup statistics
        """
        try:
            print(f"🧹 Cleaning up chat histories older than {days_old} days")
            
            # Delete old chat histories
            result = self.deps.supabase.from_('chat_histories') \
                .delete() \
                .lt('created_at', f'now() - interval \'{days_old} days\'') \
                .execute()
            
            deleted_count = len(result.data) if result.data else 0
            print(f"✅ Cleaned up {deleted_count} old chat messages")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "days_old": days_old
            }
            
        except Exception as e:
            print(f"❌ Error cleaning up old sessions: {e}")
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0
            }
    
    async def _get_session_stats(self, video_id: str, session_id: str) -> Dict:
        """
        Get conversation statistics for debugging and monitoring.
        
        Args:
            video_id: YouTube video ID
            session_id: Session identifier
            
        Returns:
            Dict: Comprehensive session statistics
        """
        try:
            # Get message counts by role
            result = self.deps.supabase.from_('chat_histories') \
                .select('role', count='exact') \
                .eq('video_id', video_id) \
                .eq('session_id', session_id) \
                .execute()
            
            # Count messages by role
            role_counts = {}
            if result.data:
                for row in result.data:
                    role = row.get('role', 'unknown')
                    role_counts[role] = role_counts.get(role, 0) + 1
            
            # Get conversation date range
            date_result = self.deps.supabase.from_('chat_histories') \
                .select('timestamp') \
                .eq('video_id', video_id) \
                .eq('session_id', session_id) \
                .order('timestamp') \
                .limit(1) \
                .execute()
            
            first_message = date_result.data[0]['timestamp'] if date_result.data else None
            
            date_result = self.deps.supabase.from_('chat_histories') \
                .select('timestamp') \
                .eq('video_id', video_id) \
                .eq('session_id', session_id) \
                .order('timestamp', desc=True) \
                .limit(1) \
                .execute()
            
            last_message = date_result.data[0]['timestamp'] if date_result.data else None
            
            stats = {
                "video_id": video_id,
                "session_id": session_id,
                "message_counts": role_counts,
                "total_messages": sum(role_counts.values()),
                "user_messages": role_counts.get('user', 0),
                "assistant_messages": role_counts.get('assistant', 0),
                "summaries": role_counts.get('summary', 0),
                "first_message": first_message,
                "last_message": last_message,
                "conversation_active": role_counts.get('user', 0) > 0
            }
            
            print(f"📊 Session stats for {video_id}: {stats['total_messages']} total messages")
            return stats
            
        except Exception as e:
            print(f"❌ Error getting session stats for video {video_id}: {e}")
            return {
                "video_id": video_id,
                "session_id": session_id,
                "error": str(e),
                "total_messages": 0
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