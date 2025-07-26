from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import requests
import subprocess
import json
import tempfile
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

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

def get_transcript_with_ytdlp(video_url, video_id):
    """Get transcript using yt-dlp"""
    # Create a temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            # Download subtitles using yt-dlp
            cmd = [
                'yt-dlp',
                '--write-auto-subs',
                '--sub-langs', 'en',
                '--sub-format', 'vtt',
                '--skip-download',
                video_url
            ]

            subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Find the downloaded subtitle file
            current_dir = Path('.')
            subtitle_files = []

            # Look for files containing the video ID
            all_files = list(current_dir.glob("*.vtt"))
            for file in all_files:
                if video_id in file.name and '.en.' in file.name:
                    subtitle_files.append(file)

            # If no English files found, look for any subtitle files with the video ID
            if not subtitle_files:
                for file in all_files:
                    if video_id in file.name:
                        subtitle_files.append(file)

            if not subtitle_files:
                raise Exception("No subtitle files found")

            # Read and parse the VTT file
            subtitle_file = subtitle_files[0]
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                vtt_content = f.read()

            # Parse VTT content into structured format
            transcript_data = parse_vtt_content(vtt_content)

            return transcript_data

        finally:
            # Change back to original directory
            os.chdir(original_cwd)

def parse_vtt_content(vtt_content):
    """Parse VTT content into structured transcript data"""
    lines = vtt_content.split('\n')
    transcript_data = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for timestamp lines (format: "00:00:00.000 --> 00:00:03.000")
        if '-->' in line:
            # Parse timestamp
            parts = line.split(' --> ')
            if len(parts) == 2:
                start_time_str = parts[0].strip()
                end_time_str = parts[1].strip()

                # Convert to seconds
                start_seconds = time_str_to_seconds(start_time_str)
                end_seconds = time_str_to_seconds(end_time_str)

                # Get the text (next non-empty line)
                text_lines = []
                i += 1
                while i < len(lines) and lines[i].strip():
                    text_lines.append(lines[i].strip())
                    i += 1

                if text_lines:
                    text = ' '.join(text_lines)
                    # Remove VTT formatting tags
                    text = re.sub(r'<[^>]+>', '', text)

                    transcript_data.append({
                        "start": start_time_str,
                        "end": end_time_str,
                        "text": text,
                        "start_seconds": start_seconds
                    })

        i += 1

    return transcript_data

def time_str_to_seconds(time_str):
    """Convert time string (HH:MM:SS.mmm) to seconds"""
    try:
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
        return total_seconds
    except:
        return 0

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Flask server is running"})

def send_transcript_to_n8n(video_id, video_title, video_url, channel, transcript_data):
    """Send transcript data to n8n for processing and storage"""
    try:
        n8n_payload = {
            "video_id": video_id,
            "title": video_title,
            "url": video_url,
            "channel": channel,
            "transcript": transcript_data
        }

        print(n8n_payload)

        print(f"\n📤 SENDING TRANSCRIPT TO N8N")
        print(f"   Video ID: {video_id}")
        print(f"   Title: {video_title}")
        print(f"   URL: {video_url}")
        print(f"   Channel: {channel}")
        print(f"   Transcript chunks: {len(transcript_data)}")
        print(f"   Endpoint: https://taddaifor.app.n8n.cloud/webhook/youtube-transcript")
        print(f"   Payload size: {len(json.dumps(n8n_payload))} bytes")

        response = requests.post(
            "https://taddaifor.app.n8n.cloud/webhook/youtube-transcript",
            json=n8n_payload,
            headers={
                "Content-Type": "application/json",
                "RAGHeader": "RAGHeader"
            },
            timeout=30
        )

        print(f"\n📥 N8N TRANSCRIPT RESPONSE")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        print(f"   Response Body: {response.text}")

        if response.status_code == 200:
            print(f"✅ Successfully sent transcript to n8n for video {video_id}")
            return True
        else:
            print(f"❌ Failed to send transcript to n8n: {response.status_code} {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending transcript to n8n: {e}")
        return False

@app.route('/transcript', methods=['POST'])
def get_transcript():
    """Get transcript for a YouTube video and send to n8n"""
    try:
        data = request.get_json()
        youtube_url = data.get('url')

        if not youtube_url:
            return jsonify({"error": "YouTube URL is required"}), 400

        # Extract video ID
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({"error": "Could not extract video ID from URL"}), 400

        # Get video title
        video_title = get_video_title(video_id)

        # Get transcript using yt-dlp
        transcript_data = get_transcript_with_ytdlp(youtube_url, video_id)

        # Extract channel name (simplified - you can enhance this)
        channel = "Unknown Channel"  # You can enhance this by parsing the YouTube page

        # Send transcript to n8n for processing and storage
        n8n_success = send_transcript_to_n8n(video_id, video_title, youtube_url, channel, transcript_data)

        # Return structured response
        response = {
            "success": True,
            "video_id": video_id,
            "title": video_title,
            "url": youtube_url,
            "language": "English",
            "language_code": "en",
            "transcript": transcript_data,
            "n8n_stored": n8n_success
        }

        return jsonify(response)

    except Exception as e:
        error_message = str(e)
        print(f"Error getting transcript: {error_message}")

        return jsonify({
            "success": False,
            "error": error_message
        }), 500

@app.route('/chat', methods=['POST'])
def chat_with_video():
    """Chat about a video using the n8n AI agent"""
    try:
        data = request.get_json()
        chat_input = data.get('chatInput')
        video_id = data.get('video_id')
        session_id = data.get('sessionId', video_id)  # Use video_id as default session

        if not chat_input:
            return jsonify({"error": "chatInput is required"}), 400

        if not video_id:
            return jsonify({"error": "video_id is required"}), 400

        # Send chat request to n8n
        n8n_payload = {
            "chatInput": chat_input,
            "video_id": video_id,
            "sessionId": session_id
        }

        print(f"\n💬 SENDING CHAT TO N8N")
        print(f"   Chat Input: {chat_input}")
        print(f"   Video ID: {video_id}")
        print(f"   Session ID: {session_id}")
        print(f"   Endpoint: https://taddaifor.app.n8n.cloud/webhook/youtube-chat")

        response = requests.post(
            "https://taddaifor.app.n8n.cloud/webhook/youtube-chat",
            json=n8n_payload,
            headers={
                "Content-Type": "application/json",
                "RAGHeader": "RAGHeader"
            },
            timeout=30
        )

        print(f"\n🤖 N8N CHAT RESPONSE")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        print(f"   Response Body: {response.text[:500]}{'...' if len(response.text) > 500 else ''}")

        if response.status_code == 200:
            print(f"✅ Successfully got chat response for video {video_id}")
            # Return the raw n8n response for now
            return jsonify({
                "success": True,
                "raw_response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            })
        else:
            print(f"❌ Failed to get chat response: {response.status_code} {response.text}")
            return jsonify({
                "success": False,
                "error": f"n8n request failed: {response.status_code} {response.text}"
            }), 500

    except Exception as e:
        error_message = str(e)
        print(f"❌ Error in chat: {error_message}")

        return jsonify({
            "success": False,
            "error": error_message
        }), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Server will be available at http://localhost:8080")
    print("Endpoints:")
    print("  - Health check: GET http://localhost:8080/health")
    print("  - Get transcript: POST http://localhost:8080/transcript")
    print("  - Chat with video: POST http://localhost:8080/chat")
    print("Integrated with n8n production endpoints")
    app.run(debug=True, host='0.0.0.0', port=8080)
