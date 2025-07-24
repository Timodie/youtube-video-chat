import sys
import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    # Handle different YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # If no pattern matches, assume it's already a video ID
    return url

def get_video_title(video_id):
    """Get video title from YouTube"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url)
        response.raise_for_status()

        # Extract title from the page HTML
        title_match = re.search(r'"title":"([^"]+)"', response.text)
        if title_match:
            title = title_match.group(1)
            # Decode unicode escape sequences
            title = title.encode().decode('unicode-escape')
            return title

        # Fallback pattern
        title_match = re.search(r'<title>([^<]+)</title>', response.text)
        if title_match:
            title = title_match.group(1)
            # Remove " - YouTube" suffix if present
            title = re.sub(r' - YouTube$', '', title)
            return title

        return "Unknown Title"
    except Exception as e:
        print(f"Could not fetch video title: {e}")
        return "Unknown Title"

# Get YouTube URL from command line argument
if len(sys.argv) != 2:
    print("Usage: python transcribeYoutubeVideo.py <youtube_url>")
    sys.exit(1)

youtube_url = sys.argv[1]
video_id = extract_video_id(youtube_url)

# Get video title
print(f"Fetching video title...")
video_title = get_video_title(video_id)
print(f"Video: {video_title}")

try:
    print(f"Attempting to get transcript for video ID: {video_id}")

    # Get auto-generated transcript specifically
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    print(f"Successfully fetched auto-generated transcript with {len(transcript_data)} entries")

    # Print the transcript
    print(f"\nTranscript for video ID: {video_id}")
    print(f"Language: English")
    print("-" * 50)

    # Convert to VTT format
    vtt_content = []
    for snippet in transcript_data:
        start_time = snippet['start']
        end_time = snippet['start'] + snippet['duration']

        # Format time as HH:MM:SS.mmm
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

        vtt_content.append(f"{format_time(start_time)} --> {format_time(end_time)}")
        vtt_content.append(snippet['text'])
        vtt_content.append("")  # Empty line between entries

        print(f"[{snippet['start']:.1f}s] {snippet['text']}")

    # Create file content with title and URL first, then VTT content
    file_content = f"Title: {video_title}\nURL: {youtube_url}\n\n" + "\n".join(vtt_content)

    # Clean title for filename (remove invalid characters)
    clean_title = re.sub(r'[<>:"/\\|?*]', '', video_title)
    clean_title = clean_title.replace(' ', '_')

    # Save to a file
    output_file = f"{clean_title}_transcript.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(file_content)

    print(f"\nTranscript saved to {output_file}")

except Exception as e:
    print(f"An error occurred: {str(e)}")
    print(f"Video ID extracted: {video_id}")
    print(f"Original URL: {youtube_url}")

    # Try with different language options
    try:
        print("Trying to get any available transcript...")
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        print(f"Found transcript with {len(transcript_data)} entries")
    except Exception as e2:
        print(f"No transcript available: {str(e2)}")
