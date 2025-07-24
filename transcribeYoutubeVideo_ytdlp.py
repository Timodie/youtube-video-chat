#!/usr/bin/env python3

import sys
import re
import json
import subprocess
from pathlib import Path

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return url

def get_video_info_and_transcript(video_url):
    """Get video info and transcript using yt-dlp"""
    try:
        # Get video info and download subtitles
        cmd = [
            'yt-dlp',
            '--write-auto-subs',
            '--sub-langs', 'en',
            '--sub-format', 'vtt',
            '--skip-download',
            '--print', 'title',
            '--print', 'id',
            video_url
        ]
        
        print("Fetching video info and transcript...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse the output (title and id are printed on separate lines)
        lines = result.stdout.strip().split('\n')
        title = lines[0] if len(lines) > 0 else 'Unknown Title'
        video_id = lines[1] if len(lines) > 1 else extract_video_id(video_url)
        
        print(f"Video: {title}")
        print(f"Video ID: {video_id}")
        
        # Look for subtitle files - yt-dlp creates files with the format: "title [video_id].lang.ext"
        current_dir = Path('.')
        subtitle_files = []
        
        # Look for files containing the video ID
        all_files = list(current_dir.glob("*.vtt")) + list(current_dir.glob("*.srt"))
        for file in all_files:
            if video_id in file.name and '.en.' in file.name:
                subtitle_files.append(file)
        
        # If no English files found, look for any subtitle files with the video ID
        if not subtitle_files:
            for file in all_files:
                if video_id in file.name:
                    subtitle_files.append(file)
        
        if subtitle_files:
            subtitle_file = subtitle_files[0]
            print(f"Found subtitle file: {subtitle_file}")
            
            # Read and process the subtitle file
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean title for output filename
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
            clean_title = clean_title.replace(' ', '_')
            
            # Create output content
            output_content = f"Title: {title}\nURL: {video_url}\n\n{content}"
            
            # Save to output file
            output_file = f"{clean_title}_transcript.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_content)
            
            print(f"Transcript saved to {output_file}")
            
            # Clean up the subtitle file
            subtitle_file.unlink()
            
            return True
        else:
            print("No subtitle files found. The video might not have auto-generated subtitles.")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error running yt-dlp: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transcribeYoutubeVideo_ytdlp.py <youtube_url>")
        sys.exit(1)
    
    youtube_url = sys.argv[1]
    success = get_video_info_and_transcript(youtube_url)
    
    if not success:
        print("Failed to get transcript. Make sure the video has auto-generated subtitles.")
        sys.exit(1)