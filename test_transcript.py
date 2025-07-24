#!/usr/bin/env python3

from youtube_transcript_api import YouTubeTranscriptApi
import sys

def test_transcript(video_id):
    """Test transcript fetching with various methods"""
    print(f"Testing transcript for video ID: {video_id}")
    
    # Method 1: Direct get_transcript
    try:
        print("Method 1: Direct get_transcript...")
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        print(f"✅ Success! Found {len(transcript_data)} transcript entries")
        return transcript_data
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
    
    # Method 2: With language specification
    try:
        print("Method 2: With English language specification...")
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        print(f"✅ Success! Found {len(transcript_data)} transcript entries")
        return transcript_data
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
    
    # Method 3: List transcripts first
    try:
        print("Method 3: List transcripts first...")
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print("Available transcripts:")
        for transcript in transcript_list:
            print(f"  - {transcript.language} ({transcript.language_code})")
        
        # Get the first available transcript
        transcript = next(iter(transcript_list))
        transcript_data = transcript.fetch()
        print(f"✅ Success! Found {len(transcript_data)} transcript entries")
        return transcript_data
    except Exception as e:
        print(f"❌ Method 3 failed: {e}")
    
    print("❌ All methods failed")
    return None

if __name__ == "__main__":
    # Test with a known working video ID
    test_video_ids = [
        "jpSY4MlWX50",  # The problematic video
        "dQw4w9WgXcQ",  # Rick Roll (known to have transcripts)
        "9bZkp7q19f0",  # Gangnam Style (known to have transcripts)
    ]
    
    for video_id in test_video_ids:
        print(f"\n{'='*50}")
        print(f"Testing video: https://www.youtube.com/watch?v={video_id}")
        print(f"{'='*50}")
        
        result = test_transcript(video_id)
        if result:
            print(f"First few entries:")
            for i, entry in enumerate(result[:3]):
                print(f"  {entry['start']:.1f}s: {entry['text']}")
            break
        print()