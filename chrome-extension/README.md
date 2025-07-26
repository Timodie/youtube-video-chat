# YouTube Transcript RAG Chrome Extension (React)

A Chrome extension built with React that extracts YouTube transcripts and enables AI-powered chat about video content.

## 🚀 Features

- **Instant Transcript Extraction** with caching
- **AI Chat** powered by RAG (Retrieval Augmented Generation)
- **Progressive Enhancement** - transcript loads instantly, chat when ready
- **Clickable Timestamps** for video navigation
- **Real-time Status Updates** with polling
- **Modern React Architecture** with hooks and state management

## 📁 Project Structure

```
chrome-extension/
├── src/
│   ├── components/
│   │   ├── Sidebar.jsx          # Main sidebar container
│   │   ├── TranscriptTab.jsx    # Transcript display and interaction
│   │   ├── ChatTab.jsx          # AI chat interface
│   │   └── TranscriptButton.jsx # YouTube page injection button
│   ├── hooks/
│   │   ├── useVideoId.js        # Track current video ID
│   │   ├── useTranscript.js     # Transcript state management
│   │   └── useChat.js           # Chat state and polling
│   ├── services/
│   │   └── api.js               # Flask server API integration
│   └── content.jsx              # Main content script entry point
├── dist/                        # Built files (generated)
├── content.css                  # Existing styles (unchanged)
├── manifest.json               # Chrome extension manifest
├── vite.config.js              # Vite build configuration
└── package.json                # Dependencies and scripts
```

## 🛠️ Development

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Flask server running on localhost:8080

### Setup
```bash
# Install dependencies
npm install

# Development build with watch mode
npm run dev

# Production build
npm run build
```

### Loading the Extension
1. Build the extension: `npm run build`
2. Open Chrome and go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked" and select this directory
5. Navigate to any YouTube video and click "📝 Get Transcript"

## 🔧 Technical Details

### State Management
- **useVideoId**: Tracks current YouTube video with SPA navigation support
- **useTranscript**: Manages transcript fetching, caching, and error states  
- **useChat**: Handles AI chat, status polling, and message history

### API Integration
- **YouTubeTranscriptAPI**: Clean service layer for Flask server communication
- **Progressive Enhancement**: Transcript loads instantly, chat polls for readiness
- **Error Handling**: Comprehensive error states and retry mechanisms

### Build Process
- **Vite**: Fast build tool optimized for modern web development
- **React 18**: Latest React with concurrent features
- **ES Modules**: Modern JavaScript module system
- **Source Maps**: Development debugging support

## 🎯 Key React Benefits

1. **Better State Management**: Centralized state with React hooks
2. **Component Reusability**: Modular, testable components
3. **Developer Experience**: Hot reload, better debugging, modern tooling
4. **Performance**: Virtual DOM, optimized re-renders
5. **Maintainability**: Clear separation of concerns, TypeScript ready