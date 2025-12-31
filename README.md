# YouTube Video Chat

A Chrome extension and Flask server that extracts transcripts from YouTube videos, with plans to add AI-powered chat functionality.

## Features

- 🎥 **Chrome Extension**: Adds a transcript button to YouTube video pages
- 📝 **Transcript Extraction**: Uses yt-dlp to reliably get auto-generated subtitles
- 🖥️ **Flask API**: REST API for transcript processing
- 🎯 **Video Navigation**: Click transcript timestamps to jump to specific moments
- 🚀 **Future**: AI chat with video content (coming soon!)

## Project Structure

```
├── chrome-extension/     # Chrome extension files
│   ├── manifest.json    # Extension configuration
│   ├── content.js       # Script that runs on YouTube pages
│   ├── content.css      # Styles for the transcript UI
│   ├── popup.html       # Extension popup interface
│   └── popup.js         # Popup functionality
├── flask-server/        # Flask API server
│   ├── app.py          # Main Flask application
│   └── requirements.txt # Python dependencies
├── transcribeYoutubeVideo.py      # Standalone script (youtube-transcript-api)
├── transcribeYoutubeVideo_ytdlp.py # Standalone script (yt-dlp)
└── test_transcript.py   # Testing utilities
```

## Installation & Setup

### 1. Flask Server

```bash
cd flask-server
pip install -r requirements.txt
python app.py
```

Server runs on `http://localhost:5001`

### 2. Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked" and select the `chrome-extension` folder
4. The extension will appear in your toolbar

### 3. Usage

1. Start the Flask server
2. Navigate to any YouTube video
3. Look for the "📝 Get Transcript" button next to like/dislike buttons
4. Click it to open the transcript sidebar
5. Click any transcript line to jump to that moment in the video

## Dependencies

- **Python**: Flask, yt-dlp, requests
- **Chrome Extension**: No external dependencies
- **System**: yt-dlp requires Python 3.7+

## API Endpoints

- `GET /health` - Health check
- `POST /transcript` - Extract transcript from YouTube URL

### Transcript API Example

```bash
curl -X POST http://localhost:5001/transcript \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

## Future Features

- 🤖 AI-powered chat with video content
- 📋 Transcript summaries
- 🔍 Semantic search through transcripts
- 💾 Save and organize transcripts
- 🌐 Support for more video platforms

## Development

The project uses yt-dlp for reliable transcript extraction, replacing the less reliable youtube-transcript-api. The Chrome extension communicates with the Flask server via REST API.

## Contributing

Feel free to open issues and submit pull requests!
