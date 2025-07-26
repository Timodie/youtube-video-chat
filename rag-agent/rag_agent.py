from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import logfire
import asyncio
import httpx
import os

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from supabase import Client
from typing import List

load_dotenv()

llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')
model = OpenAIModel(llm)

logfire.configure(send_to_logfire='if-token-present')

@dataclass
class PydanticAIDeps:
    supabase: Client
    openai_client: AsyncOpenAI

system_prompt = """
You are a YouTube Video Assistant powered by RAG (Retrieval Augmented Generation). You help users understand and navigate the YouTube video they are currently watching.

## Context:
- The user is currently watching a specific YouTube video
- The video_id is automatically provided with each question
- All questions should be assumed to be about the current video unless explicitly stated otherwise

## Your Capabilities:
- Answer questions about the current video's content
- Provide exact quotes and timestamps for navigation
- Summarize video sections or overall content
- Help users find specific moments or topics within the video

## Your Behavior:
- Always search the current video's transcript data first
- Include clickable timestamps in your responses: [MM:SS] format
- Provide specific quotes from the transcript
- If information isn't found in this video's transcript, say so clearly
- Help users navigate to relevant moments in the video

## Response Format:
- Answer the question directly using transcript content
- Include relevant quotes: "The video says: '[exact quote]'"
- Provide timestamps for navigation: "This happens at [MM:SS]"
- Be conversational but precise

## Example Responses:
- "At [01:23], the video explains: '[quote from transcript]'"
- "This topic is covered at [02:45] where it says: '[quote]'"
- "I couldn't find information about that topic in this video's transcript"

Always search the transcript first, then provide helpful, timestamped responses to help users navigate and understand the current video.
"""

youtube_ai_assistant = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=PydanticAIDeps,
    retries=2
)

async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error

@youtube_ai_assistant.tool
async def search_video_transcript(ctx: RunContext[PydanticAIDeps], user_query: str, video_id: str) -> str:
    """
    Search within a specific video's transcript using RAG.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The user's question or query
        video_id: YouTube video ID to search within

    Returns:
        A formatted string containing the most relevant transcript chunks with timestamps
    """
    try:
        # Get the embedding for the query
        query_embedding = await get_embedding(user_query, ctx.deps.openai_client)

        # Query Supabase for relevant transcript chunks within the specific video
        result = ctx.deps.supabase.rpc(
            'match_youtube_transcript_pages',
            {
                'query_embedding': query_embedding,
                'match_count': 5,
                'filter': {'video_id': video_id}
            }
        ).execute()

        if not result.data:
            return f"No relevant content found in video {video_id} for your query."

        # Format the results with timestamps for video navigation
        formatted_chunks = []
        for doc in result.data:
            # Extract timestamp info from metadata
            start_time = doc['metadata'].get('start_time', 'Unknown')
            end_time = doc['metadata'].get('end_time', 'Unknown')
            
            chunk_text = f"""
**[{start_time} - {end_time}]**
{doc['content']}

Similarity: {doc['similarity']:.3f}
"""
            formatted_chunks.append(chunk_text)

        # Join all chunks with a separator
        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        print(f"Error searching video transcript: {e}")
        return f"Error searching video transcript: {str(e)}"

@youtube_ai_assistant.tool
async def get_video_timeline(ctx: RunContext[PydanticAIDeps], video_id: str) -> str:
    """
    Get chronological overview of video content with timestamps.

    Args:
        ctx: The context including the Supabase client
        video_id: YouTube video ID to get timeline for

    Returns:
        str: Chronological list of all transcript chunks with timestamps
    """
    try:
        # Query Supabase for all chunks of this video, ordered by chunk_number
        result = ctx.deps.supabase.from_('youtube_transcript_pages') \
            .select('content, metadata, chunk_number') \
            .eq('video_id', video_id) \
            .order('chunk_number') \
            .execute()

        if not result.data:
            return f"No transcript found for video {video_id}."

        # Format the timeline
        timeline_entries = []
        for chunk in result.data:
            start_time = chunk['metadata'].get('start_time', 'Unknown')
            end_time = chunk['metadata'].get('end_time', 'Unknown')
            content_preview = chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
            
            timeline_entry = f"[{start_time} - {end_time}]: {content_preview}"
            timeline_entries.append(timeline_entry)

        return "\n\n".join(timeline_entries)

    except Exception as e:
        print(f"Error retrieving video timeline: {e}")
        return f"Error retrieving video timeline: {str(e)}"

@youtube_ai_assistant.tool
async def get_video_summary(ctx: RunContext[PydanticAIDeps], video_id: str) -> str:
    """
    Get video metadata and overall summary.

    Args:
        ctx: The context including the Supabase client
        video_id: YouTube video ID to get summary for

    Returns:
        str: Video metadata including title, URL, duration, and content overview
    """
    try:
        # Query Supabase for video metadata from the first chunk
        result = ctx.deps.supabase.from_('youtube_transcript_pages') \
            .select('title, url, metadata') \
            .eq('video_id', video_id) \
            .eq('chunk_number', 0) \
            .execute()

        if not result.data:
            return f"No video found with ID: {video_id}"

        video_data = result.data[0]
        
        # Get total chunk count for duration estimate
        count_result = ctx.deps.supabase.from_('youtube_transcript_pages') \
            .select('chunk_number', count='exact') \
            .eq('video_id', video_id) \
            .execute()

        total_chunks = count_result.count if count_result.count else 0

        # Extract video title (remove timestamp part if present)
        full_title = video_data['title']
        video_title = full_title.split(' (')[0] if ' (' in full_title else full_title
        
        # Format summary
        summary = f"""
**Video Information:**
- Title: {video_title}
- Video ID: {video_id}
- URL: {video_data['url']}
- Total transcript chunks: {total_chunks}

**Video Overview:**
This video has been processed into {total_chunks} searchable transcript segments. You can ask specific questions about the content, request timestamps for navigation, or search for particular topics within the video.
"""

        return summary

    except Exception as e:
        print(f"Error retrieving video summary: {e}")
        return f"Error retrieving video summary: {str(e)}"
