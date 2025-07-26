import pytest
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug: Print the environment variables being used
print("🔍 DEBUGGING ENVIRONMENT VARIABLES:")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT SET')[:20]}..." if os.getenv('OPENAI_API_KEY') else "OPENAI_API_KEY: NOT SET")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NOT SET')}")
print(f"SUPABASE_SERVICE_KEY: {os.getenv('SUPABASE_SERVICE_KEY', 'NOT SET')[:20]}..." if os.getenv('SUPABASE_SERVICE_KEY') else "SUPABASE_SERVICE_KEY: NOT SET")
print(f"LLM_MODEL: {os.getenv('LLM_MODEL', 'NOT SET')}")
print("=" * 50)

from ingest_youtube import chunk_vtt_transcript


class TestChunkVttTranscript:
    """Test cases for the chunk_vtt_transcript function."""
    
    def test_basic_chunking(self):
        """Test basic chunking with default parameters."""
        # Sample transcript data matching Flask server output (with end_seconds)
        transcript_data = [
            {"start": "00:00:00.000", "end": "00:00:03.000", "text": "Hello everyone", "start_seconds": 0.0, "end_seconds": 3.0},
            {"start": "00:00:03.000", "end": "00:00:06.000", "text": "Welcome to this video", "start_seconds": 3.0, "end_seconds": 6.0},
            {"start": "00:00:06.000", "end": "00:00:09.000", "text": "Today we'll discuss", "start_seconds": 6.0, "end_seconds": 9.0},
            {"start": "00:00:09.000", "end": "00:00:12.000", "text": "Some important topics", "start_seconds": 9.0, "end_seconds": 12.0},
            {"start": "00:00:12.000", "end": "00:00:15.000", "text": "That you should know", "start_seconds": 12.0, "end_seconds": 15.0},
        ]
        
        chunks = chunk_vtt_transcript(transcript_data, entries_per_chunk=3)
        
        # Should create 2 chunks (3 entries + 2 entries)
        assert len(chunks) == 2
        
        # Check first chunk
        first_chunk = chunks[0]
        assert first_chunk['text'] == "Hello everyone Welcome to this video Today we'll discuss"
        assert first_chunk['start_time'] == "00:00:00.000"
        assert first_chunk['end_time'] == "00:00:09.000"
        assert first_chunk['start_seconds'] == 0.0
        assert first_chunk['duration'] == 9.0  # 9.0 - 0.0 (end of last entry in chunk)
        assert first_chunk['entry_count'] == 3
        
        # Check second chunk
        second_chunk = chunks[1]
        assert second_chunk['text'] == "Some important topics That you should know"
        assert second_chunk['start_time'] == "00:00:09.000"
        assert second_chunk['end_time'] == "00:00:15.000"
        assert second_chunk['start_seconds'] == 9.0
        assert second_chunk['entry_count'] == 2
    
    def test_single_entry_chunk(self):
        """Test chunking with single entry per chunk."""
        transcript_data = [
            {"start": "00:00:00.000", "end": "00:00:03.000", "text": "First sentence", "start_seconds": 0.0},
            {"start": "00:00:03.000", "end": "00:00:06.000", "text": "Second sentence", "start_seconds": 3.0},
        ]
        
        chunks = chunk_vtt_transcript(transcript_data, entries_per_chunk=1)
        
        assert len(chunks) == 2
        assert chunks[0]['text'] == "First sentence"
        assert chunks[0]['entry_count'] == 1
        assert chunks[1]['text'] == "Second sentence"
        assert chunks[1]['entry_count'] == 1
    
    def test_large_chunk_size(self):
        """Test chunking when chunk size is larger than available entries."""
        transcript_data = [
            {"start": "00:00:00.000", "end": "00:00:03.000", "text": "Only entry", "start_seconds": 0.0},
        ]
        
        chunks = chunk_vtt_transcript(transcript_data, entries_per_chunk=5)
        
        assert len(chunks) == 1
        assert chunks[0]['text'] == "Only entry"
        assert chunks[0]['entry_count'] == 1
    
    def test_empty_transcript(self):
        """Test handling of empty transcript data."""
        transcript_data = []
        
        chunks = chunk_vtt_transcript(transcript_data)
        
        assert len(chunks) == 0
    
    def test_end_seconds_fallback(self):
        """Test fallback when end_seconds is not provided."""
        transcript_data = [
            {"start": "00:00:00.000", "end": "00:00:03.000", "text": "Test text", "start_seconds": 0.0},
            # Missing end_seconds - should use fallback
        ]
        
        chunks = chunk_vtt_transcript(transcript_data, entries_per_chunk=1)
        
        assert len(chunks) == 1
        # Should use start_seconds + 15 as fallback for end_seconds
        assert chunks[0]['end_seconds'] == 15.0  # 0.0 + 15
        assert chunks[0]['duration'] == 15.0
    
    def test_text_combination(self):
        """Test that text from multiple entries is properly combined."""
        transcript_data = [
            {"start": "00:00:00.000", "end": "00:00:02.000", "text": "First", "start_seconds": 0.0},
            {"start": "00:00:02.000", "end": "00:00:04.000", "text": "Second", "start_seconds": 2.0},
            {"start": "00:00:04.000", "end": "00:00:06.000", "text": "Third", "start_seconds": 4.0},
        ]
        
        chunks = chunk_vtt_transcript(transcript_data, entries_per_chunk=3)
        
        assert len(chunks) == 1
        assert chunks[0]['text'] == "First Second Third"
    
    def test_realistic_youtube_data(self):
        """Test with realistic YouTube transcript data structure."""
        # This mimics the structure from your Flask server's parse_vtt_content function
        transcript_data = [
            {
                "start": "00:00:15.120",
                "end": "00:00:18.720", 
                "text": "In this tutorial we're going to learn",
                "start_seconds": 15.12,
                "end_seconds": 18.72
            },
            {
                "start": "00:00:18.720",
                "end": "00:00:22.080",
                "text": "how to build a simple web application",
                "start_seconds": 18.72,
                "end_seconds": 22.08
            },
            {
                "start": "00:00:22.080", 
                "end": "00:00:25.440",
                "text": "using Python and Flask framework",
                "start_seconds": 22.08,
                "end_seconds": 25.44
            }
        ]
        
        chunks = chunk_vtt_transcript(transcript_data, entries_per_chunk=2)
        
        assert len(chunks) == 2
        
        # First chunk should combine first 2 entries
        first_chunk = chunks[0]
        expected_text = "In this tutorial we're going to learn how to build a simple web application"
        assert first_chunk['text'] == expected_text
        assert first_chunk['start_time'] == "00:00:15.120"
        assert first_chunk['end_time'] == "00:00:22.080"
        assert first_chunk['start_seconds'] == 15.12
        assert first_chunk['end_seconds'] == 22.08
        assert first_chunk['entry_count'] == 2
        
        # Second chunk should have remaining entry
        second_chunk = chunks[1]
        assert second_chunk['text'] == "using Python and Flask framework"
        assert second_chunk['entry_count'] == 1


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])