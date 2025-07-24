# YouTube Transcript Extractor Chrome Extension

A Chrome extension that adds a transcript extraction button to YouTube video pages.

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right
3. Click "Load unpacked" and select the `chrome-extension` folder
4. The extension should now appear in your extensions list

## Usage

1. Navigate to any YouTube video
2. Look for the "📝 Get Transcript" button next to the like/dislike buttons
3. Click the button to extract the transcript (currently shows video info as placeholder)

## Files Structure

- `manifest.json` - Extension configuration
- `content.js` - Script that runs on YouTube pages
- `content.css` - Styles for the transcript button
- `popup.html` - Extension popup UI
- `popup.js` - Popup functionality
- `icons/` - Extension icons (placeholder)

## Current Features

- ✅ Injects transcript button on YouTube video pages
- ✅ Detects current video ID and URL
- ✅ Extension popup with status information
- ✅ Works with YouTube's single-page app navigation

## Next Steps

- Add actual transcript extraction functionality
- Connect to backend API or local Python script
- Save transcripts locally or to cloud storage
- Add transcript formatting options