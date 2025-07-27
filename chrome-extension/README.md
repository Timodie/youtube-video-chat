# YouTube Transcript RAG Chrome Extension (React + TypeScript)

A Chrome extension built with React and TypeScript that extracts YouTube transcripts and enables AI-powered chat about video content.

## 🚀 Features

- **Instant Transcript Extraction** with caching
- **AI Chat** powered by RAG (Retrieval Augmented Generation)
- **Progressive Enhancement** - transcript loads instantly, chat when ready
- **Clickable Timestamps** for video navigation
- **Real-time Status Updates** with polling
- **Modern React + TypeScript Architecture** with hooks and full type safety
- **Memory Leak Prevention** with proper cleanup mechanisms

## 📁 Project Structure

```
chrome-extension/
├── src/
│   ├── components/
│   │   ├── Sidebar.tsx          # Main sidebar container
│   │   ├── TranscriptTab.tsx    # Transcript display and interaction
│   │   ├── ChatTab.tsx          # AI chat interface
│   │   └── TranscriptButton.tsx # YouTube page injection button
│   ├── hooks/
│   │   ├── useVideoId.ts        # Track current video ID
│   │   ├── useTranscript.ts     # Transcript state management
│   │   └── useChat.ts           # Chat state and polling
│   ├── services/
│   │   └── api.ts               # Flask server API integration
│   ├── types/
│   │   └── index.ts             # TypeScript type definitions
│   └── content.tsx              # Main content script entry point
├── dist/                        # Built files (generated - load from here)
├── content.css                  # Existing styles (unchanged)
├── manifest.json               # Chrome extension manifest
├── tsconfig.json               # TypeScript configuration
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

# TypeScript type checking
npm run type-check
```

### Loading the Extension
1. Build the extension: `npm run build`
2. Open Chrome and go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked" and select the **`dist`** folder (not the root directory)
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
- **TypeScript**: Full type safety with strict mode enabled
- **ES Modules**: Modern JavaScript module system
- **Source Maps**: Development debugging support
- **Automatic File Copying**: Extension files automatically copied to dist/

### Memory Management
- **Proper Cleanup**: All timers, intervals, and React roots are cleaned up
- **useRef Pattern**: Timeout and interval references tracked for cleanup
- **Component Lifecycle**: Cleanup on unmount and video changes
- **Chrome Extension Lifecycle**: Handles extension reload/unload

## 🎯 Key TypeScript + React Benefits

1. **Type Safety**: Comprehensive TypeScript interfaces for all data structures
2. **Better State Management**: Centralized state with typed React hooks
3. **Component Reusability**: Modular, testable components with prop types
4. **Developer Experience**: IntelliSense, compile-time error checking, refactoring
5. **Memory Safety**: Proper cleanup prevents browser memory leaks
6. **Maintainability**: Clear separation of concerns, self-documenting code