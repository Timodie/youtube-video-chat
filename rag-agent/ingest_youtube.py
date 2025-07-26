import os
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from dotenv import load_dotenv

from openai import AsyncOpenAI
from supabase import create_client, Client

load_dotenv()

# Initialize OpenAI and Supabase clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

@dataclass
class ProcessedChunk:
    video_id: str
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]

def chunk_vtt_transcript(transcript_data: List[Dict], entries_per_chunk: int = 3) -> List[Dict]:
    """Chunk VTT transcript data into semantic groups.

    Args:
        transcript_data: List of transcript entries with start, end, text, start_seconds
        entries_per_chunk: Number of transcript entries to group together (default: 3)

    Returns:
        List of chunks with combined text and metadata
    """
    chunks = []

    for i in range(0, len(transcript_data), entries_per_chunk):
        chunk_entries = transcript_data[i:i + entries_per_chunk]

        # Combine text from all entries in this chunk
        combined_text = ' '.join(entry['text'] for entry in chunk_entries)

        # Get start time from first entry, end time from last entry
        start_time = chunk_entries[0]['start']
        end_time = chunk_entries[-1]['end']
        start_seconds = chunk_entries[0]['start_seconds']
        end_seconds = chunk_entries[-1].get('end_seconds', start_seconds + 15)  # fallback

        chunks.append({
            'text': combined_text,
            'start_time': start_time,
            'end_time': end_time,
            'start_seconds': start_seconds,
            'end_seconds': end_seconds,
            'duration': end_seconds - start_seconds,
            'entry_count': len(chunk_entries)
        })

    return chunks

def create_title_and_summary(video_title: str, chunk_data: Dict) -> Dict[str, str]:
    """Create title and summary using template approach (no LLM needed).

    Args:
        video_title: The title of the YouTube video
        chunk_data: Chunk data with start_time, end_time, text, etc.

    Returns:
        Dict with 'title' and 'summary' keys
    """
    start_time = chunk_data['start_time']
    end_time = chunk_data['end_time']
    content = chunk_data['text']

    # Create descriptive title
    title = f"{video_title} ({start_time}-{end_time})"

    # Create summary with content preview
    content_preview = content[:100] + "..." if len(content) > 100 else content
    summary = f"Transcript from {start_time} to {end_time}: {content_preview}"

    return {
        "title": title,
        "summary": summary
    }

async def get_embedding(text: str) -> List[float]:
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

async def process_chunk(chunk_data: Dict, chunk_number: int, video_id: str, video_url: str, video_title: str) -> ProcessedChunk:
    """Process a single chunk of VTT transcript data.

    Args:
        chunk_data: Dict with text, start_time, end_time, etc.
        chunk_number: Sequential chunk number
        video_id: YouTube video ID
        video_url: Full YouTube URL
        video_title: Video title

    Returns:
        ProcessedChunk ready for database insertion
    """
    # Get title and summary using template approach
    extracted = create_title_and_summary(video_title, chunk_data)

    # Get embedding for the text content
    embedding = await get_embedding(chunk_data['text'])

    # Create metadata with YouTube-specific information
    metadata = {
        "source": video_url,
        "video_id": video_id,
        "start_time": chunk_data['start_time'],
        "end_time": chunk_data['end_time'],
        "start_seconds": chunk_data['start_seconds'],
        "end_seconds": chunk_data['end_seconds'],
        "duration": chunk_data['duration'],
        "entry_count": chunk_data['entry_count'],
        "chunk_size": len(chunk_data['text']),
        "processed_at": datetime.now(timezone.utc).isoformat()
    }

    return ProcessedChunk(
        video_id=video_id,
        url=video_url,
        chunk_number=chunk_number,
        title=extracted['title'],
        summary=extracted['summary'],
        content=chunk_data['text'],
        metadata=metadata,
        embedding=embedding
    )

async def insert_chunk(chunk: ProcessedChunk):
    """Insert a processed chunk into Supabase youtube_transcript_pages table."""
    try:
        data = {
            "video_id": chunk.video_id,
            "url": chunk.url,
            "chunk_number": chunk.chunk_number,
            "title": chunk.title,
            "summary": chunk.summary,
            "content": chunk.content,
            "metadata": chunk.metadata,
            "embedding": chunk.embedding
        }
        print(f"Attempting to Insert chunk {chunk.chunk_number} for video {chunk.video_id}")

        result = supabase.table("youtube_transcript_pages").insert(data).execute()
        print(f"Inserted chunk {chunk.chunk_number} for video {chunk.video_id}")
        return result
    except Exception as e:
        print(f"Error inserting chunk: {e}")
        return None

async def process_and_store_transcript(video_id: str, video_url: str, video_title: str, transcript_data: List[Dict]):
    """Process a YouTube transcript and store its chunks in batches to avoid rate limits.

    Args:
        video_id: YouTube video ID
        video_url: Full YouTube URL
        video_title: Video title
        transcript_data: List of transcript entries from VTT parsing
    """
    try:
        # Split transcript into semantic chunks
        chunks = chunk_vtt_transcript(transcript_data)
        print(f"Processing {len(chunks)} chunks for video {video_id}")

        # Process chunks in smaller batches to avoid overwhelming OpenAI API
        batch_size = 50  # Process 50 chunks at a time
        total_results = []
        
        for batch_start in range(0, len(chunks), batch_size):
            batch_end = min(batch_start + batch_size, len(chunks))
            batch_chunks = chunks[batch_start:batch_end]
            
            print(f"Processing batch {batch_start//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}: chunks {batch_start}-{batch_end-1}")
            
            try:
                # Process this batch of chunks in parallel
                tasks = [
                    process_chunk(chunk_data, batch_start + i, video_id, video_url, video_title)
                    for i, chunk_data in enumerate(batch_chunks)
                ]
                processed_chunks = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for exceptions in processing
                successful_chunks = []
                for i, chunk in enumerate(processed_chunks):
                    if isinstance(chunk, Exception):
                        print(f"❌ Error processing chunk {batch_start + i}: {chunk}")
                    else:
                        successful_chunks.append(chunk)
                
                print(f"Successfully processed {len(successful_chunks)}/{len(batch_chunks)} chunks in batch")
                
                # Store successful chunks in parallel
                if successful_chunks:
                    insert_tasks = [insert_chunk(chunk) for chunk in successful_chunks]
                    batch_results = await asyncio.gather(*insert_tasks, return_exceptions=True)
                    
                    # Check insertion results
                    successful_inserts = 0
                    for i, result in enumerate(batch_results):
                        if isinstance(result, Exception):
                            print(f"❌ Error inserting chunk: {result}")
                        elif result is not None:
                            successful_inserts += 1
                    
                    print(f"Successfully inserted {successful_inserts}/{len(successful_chunks)} chunks in batch")
                    total_results.extend(batch_results)
                
                # Small delay between batches to be nice to APIs
                if batch_end < len(chunks):
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error processing batch {batch_start}-{batch_end-1}: {e}")
                continue

        successful_results = [r for r in total_results if r is not None and not isinstance(r, Exception)]
        print(f"✅ Successfully stored {len(successful_results)} total chunks for video {video_id}")
        return successful_results
        
    except Exception as e:
        print(f"❌ Critical error in process_and_store_transcript: {e}")
        import traceback
        traceback.print_exc()
        return []





async def main():
    """Example usage - process a YouTube transcript.

    In practice, this function will be called by your Flask server
    with the actual video data.
    """
    # Example data - replace with actual video data from Flask server
    video_id = "dQw4w9WgXcQ"
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_title = "Rick Astley - Never Gonna Give You Up"

    # Example transcript data - replace with parsed VTT data
    transcript_data = [
        {"start": "00:00:00.000", "end": "00:00:03.000", "text": "We're no strangers to love", "start_seconds": 0.0},
        {"start": "00:00:03.000", "end": "00:00:06.000", "text": "You know the rules and so do I", "start_seconds": 3.0},
        {"start": "00:00:06.000", "end": "00:00:09.000", "text": "A full commitment's what I'm thinking of", "start_seconds": 6.0},
    ]

    print(f"Processing transcript for video: {video_title}")
    await process_and_store_transcript(video_id, video_url, video_title, transcript_data)

if __name__ == "__main__":
    asyncio.run(main())
