from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import requests
import subprocess
import json
import tempfile
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Initialize RAG integration
rag_integration = None

try:
    from rag_integration import create_rag_integration
    
    # Initialize clients for RAG
    supabase_client: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create RAG integration
    rag_integration = create_rag_integration(supabase_client, openai_client)
    
    if rag_integration:
        print("✅ RAG integration enabled")
    else:
        print("⚠️ RAG integration failed to initialize")
        
except Exception as e:
    print(f"⚠️ RAG integration not available: {e}")
    rag_integration = None

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
                        "start_seconds": start_seconds,
                        "end_seconds": end_seconds
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

        # Try RAG ingest (non-blocking) - new direct approach
        rag_stored = False
        if rag_integration:
            try:
                print(f"🔄 Attempting RAG ingest for video {video_id}")
                rag_stored = asyncio.run(rag_integration.ingest_transcript(
                    video_id=video_id,
                    video_url=youtube_url,
                    video_title=video_title,
                    transcript_data=transcript_data
                ))
                print(f"{'✅' if rag_stored else '⚠️'} RAG ingest {'succeeded' if rag_stored else 'failed'} for video {video_id}")
            except Exception as e:
                print(f"❌ RAG ingest error for video {video_id}: {e}")
                rag_stored = False
        else:
            print(f"⚠️ RAG integration not available for video {video_id}")

        # Fallback: Also try n8n for backward compatibility (optional)
        n8n_success = False
        try:
            n8n_success = send_transcript_to_n8n(video_id, video_title, youtube_url, channel, transcript_data)
        except Exception as e:
            print(f"⚠️ n8n fallback failed: {e}")

        # Return structured response (always succeeds if transcript extraction worked)
        response = {
            "success": True,
            "video_id": video_id,
            "title": video_title,
            "url": youtube_url,
            "language": "English",
            "language_code": "en",
            "transcript": transcript_data,
            "rag_stored": rag_stored,      # New RAG storage status
            "n8n_stored": n8n_success      # Legacy n8n status
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
async def chat_with_video():
    """Chat about a video using the RAG AI agent"""
    try:
        data = request.get_json()
        chat_input = data.get('chatInput')
        video_id = data.get('video_id')
        session_id = data.get('sessionId', video_id)  # Use video_id as default session

        if not chat_input:
            return jsonify({"error": "chatInput is required"}), 400

        if not video_id:
            return jsonify({"error": "video_id is required"}), 400

        print(f"\n💬 PROCESSING CHAT REQUEST")
        print(f"   Chat Input: {chat_input}")
        print(f"   Video ID: {video_id}")
        print(f"   Session ID: {session_id}")

        # Try RAG agent first (primary method)
        if rag_integration:
            try:
                print(f"🤖 Using RAG agent for video {video_id}")
                
                result = await rag_integration.chat_with_video(video_id, chat_input)
                
                if result["success"]:
                    print(f"✅ RAG agent response successful")
                    return jsonify({
                        "success": True,
                        "response": result["response"],
                        "timestamps": result.get("timestamps", []),
                        "video_id": video_id,
                        "method": "rag_agent",
                        "processed_at": result.get("processed_at")
                    })
                else:
                    print(f"⚠️ RAG agent returned error: {result.get('error', 'Unknown error')}")
                    # Continue to n8n fallback
                    
            except Exception as e:
                print(f"❌ RAG agent failed: {e}")
                # Continue to n8n fallback

        # # Fallback to n8n (if RAG failed or not available) - COMMENTED OUT FOR TESTING
        # try:
        #     print(f"🔄 Falling back to n8n for video {video_id}")
        #     
        #     n8n_payload = {
        #         "chatInput": chat_input,
        #         "video_id": video_id,
        #         "sessionId": session_id
        #     }

        #     response = requests.post(
        #         "https://taddaifor.app.n8n.cloud/webhook/youtube-chat",
        #         json=n8n_payload,
        #         headers={
        #             "Content-Type": "application/json",
        #             "RAGHeader": "RAGHeader"
        #         },
        #         timeout=30
        #     )

        #     print(f"📥 n8n response: {response.status_code}")

        #     if response.status_code == 200:
        #         print(f"✅ n8n fallback successful for video {video_id}")
        #         return jsonify({
        #             "success": True,
        #             "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
        #             "video_id": video_id,
        #             "method": "n8n_fallback",
        #             "timestamps": []  # n8n may not provide structured timestamps
        #         })
        #     else:
        #         print(f"❌ n8n fallback failed: {response.status_code}")
        #         
        # except Exception as e:
        #     print(f"❌ n8n fallback error: {e}")

        # RAG only mode - no fallback
        return jsonify({
            "success": False,
            "error": "RAG agent failed and n8n fallback is disabled for testing.",
            "video_id": video_id
        }), 500

    except Exception as e:
        error_message = str(e)
        print(f"❌ Critical error in chat endpoint: {error_message}")

        return jsonify({
            "success": False,
            "error": "Internal server error",
            "video_id": video_id if 'video_id' in locals() else None
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
