# YouTube Transcript RAG System - Development Notes

## Project Overview
A complete YouTube video chat system that extracts transcripts and enables AI-powered conversations about video content using RAG (Retrieval Augmented Generation).

## System Architecture

### Core Components
1. **Chrome Extension** - Adds transcript button to YouTube pages with tabbed sidebar (Transcript + Chat)
2. **Flask Server** - Processes YouTube transcripts using yt-dlp and proxies requests to n8n
3. **n8n Workflow** - Handles transcript chunking, vector storage, and AI chat with memory
4. **Supabase/PostgreSQL** - Vector database for semantic search and chat memory storage

### Data Flow
```
YouTube Video → Chrome Extension → Flask Server → n8n Workflow → AI Response
                     ↓                    ↓              ↓
              User Interface      yt-dlp extraction   Vector Storage
                                                      + RAG Search
```

## Technical Implementation

### 1. Chrome Extension (`chrome-extension/`)
- **Manifest v3** with content scripts for YouTube integration
- **Tabbed sidebar** with transcript display and chat interface
- **iOS-style loading animations** for chat interactions
- **Clickable timestamps** for video navigation
- **Real-time AI chat** integration with Flask backend

### 2. Flask Server (`flask-server/app.py`)
- **yt-dlp integration** for reliable transcript extraction (replaces youtube-transcript-api)
- **n8n webhook integration** for transcript processing and AI chat
- **Comprehensive logging** with emoji indicators for debugging
- **CORS enabled** for Chrome extension communication

**Key Endpoints:**
- `POST /transcript` - Extract and persist video transcripts
- `POST /chat` - AI chat about video content
- `GET /health` - Server health check

### 3. n8n Workflow (`n8n-workflows/youtube-video-workflow-clean.json`)

**Transcript Processing Pipeline:**
```
Webhook → Set Video Data → Delete Old Chunks → Process Chunks → Insert Vectorstore → Respond
```

**Chat Pipeline:**
```
Webhook → Set Chat Data → AI Agent → Respond
```

**Key Features:**
- **Video isolation** - Each video's transcripts stored separately by video_id
- **Smart chunking** - 10-15 second chunks with timestamp metadata
- **Memory management** - Postgres chat memory with session isolation
- **RAG search** - Semantic search within specific video transcripts
- **Structured output** - AI responses include clickable timestamps

## Configuration Details

### n8n Webhooks
- **Production Transcript**: `https://taddaifor.app.n8n.cloud/webhook/youtube-transcript`
- **Production Chat**: `https://taddaifor.app.n8n.cloud/webhook/youtube-chat`
- **Authentication**: `RAGHeader: RAGHeader`

### Database Schema
```sql
-- YouTube transcripts table
CREATE TABLE youtube_transcripts (
  id bigserial primary key,
  content text,
  metadata jsonb,
  embedding vector(1536),
  created_at timestamp default now()
);

-- Optimized for video_id filtering
CREATE INDEX idx_youtube_transcripts_video_id 
ON youtube_transcripts USING btree ((metadata->>'video_id'));
```

### Vector Search Function
```sql
-- Supabase-compatible function signature
CREATE OR REPLACE FUNCTION match_youtube_transcripts (
  filter jsonb,
  match_count int,
  query_embedding vector(1536)
) RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
);
```

## Key Technical Decisions

### 1. Transcript Extraction
- **Switched from youtube-transcript-api to yt-dlp** due to reliability issues
- **VTT format parsing** for timestamp preservation
- **Automatic subtitle detection** with English preference

### 2. Chunking Strategy
- **Paragraph-level chunks** (2-4 transcript entries, 10-15 seconds)
- **Preserves sentence boundaries** for better semantic coherence
- **Timestamp metadata** included in each chunk for video navigation

### 3. Vector Storage
- **Supabase/PostgreSQL** with pgvector extension
- **OpenAI text-embedding-3-small** for embeddings
- **B-tree indexing** on video_id for fast filtering

### 4. Memory Management
- **Session isolation by video_id** - Each video has separate conversation context
- **Postgres chat memory** for conversation history
- **24-hour auto-cleanup** capability (optional)

## Debugging & Troubleshooting

### Common Issues Fixed

1. **"Process Chunks not connected"**
   - Issue: Node referenced wrong data source after workflow changes
   - Solution: Updated Process Chunks to reference Set Video Data directly

2. **PostgreSQL Function Signature Mismatch**
   - Issue: Supabase expected `(filter, match_count, query_embedding)` parameters
   - Solution: Updated function signature to match Supabase's calling convention

3. **Chat Memory "3 keys" Error**
   - Issue: Memory node couldn't handle multiple input keys
   - Solution: Added `sessionIdKey: "sessionId"` parameter

4. **GIN Index Creation Error**
   - Issue: Incorrect operator class for text fields in JSONB
   - Solution: Used B-tree index with `(metadata->>'video_id')` expression

### Testing Commands

**Test Transcript Processing:**
```bash
curl -X POST "http://localhost:8080/transcript" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

**Test AI Chat:**
```bash
curl -X POST "http://localhost:8080/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "chatInput": "What is this video about?",
    "video_id": "dQw4w9WgXcQ"
  }'
```

## Development Environment

### Required Dependencies
- **Python**: Flask, requests, flask-cors
- **System**: yt-dlp (for transcript extraction)
- **Chrome Extension**: Content scripts, manifest v3
- **n8n**: LangChain nodes, OpenAI integration, Supabase vectorstore

### File Structure
```
youtube-transcript/
├── chrome-extension/
│   ├── manifest.json
│   ├── content.js
│   └── content.css
├── flask-server/
│   └── app.py
├── n8n-workflows/
│   └── youtube-video-workflow-clean.json
└── CLAUDE.md
```

## Future Enhancements

### Planned Improvements
1. **Enhanced response formatting** - Parse structured AI output for better UX
2. **Channel detection** - Extract channel name from YouTube pages
3. **Conversation export** - Save chat history for later reference
4. **Multiple language support** - Auto-detect and process non-English videos
5. **Batch processing** - Handle multiple videos simultaneously

### Performance Optimizations
1. **Caching layer** - Cache frequently accessed transcripts
2. **Streaming responses** - Real-time AI response streaming
3. **Background processing** - Async transcript processing
4. **Rate limiting** - Prevent API abuse

## Production Deployment

### Security Considerations
- **API authentication** - Secure n8n webhook endpoints
- **Input validation** - Sanitize user inputs and video URLs
- **Rate limiting** - Prevent abuse of transcript extraction
- **Error handling** - Graceful degradation for failed requests

### Monitoring
- **Comprehensive logging** - Track all n8n interactions
- **Health checks** - Monitor Flask server and n8n workflow status
- **Performance metrics** - Track response times and success rates

## Next Iteration: Direct RAG Implementation

### Current Issue
The n8n workflow approach has chunking issues that affect RAG quality. Moving to a direct Python-based RAG system for better control.

### New Architecture Plan
1. **Database**: Create `youtube_transcript_pages` table in Supabase
2. **Processing Pipeline**: VTT → Custom Chunking → OpenAI Embeddings → Database Storage
3. **RAG Agent**: Direct database queries for relevant chunks to answer questions
4. **Unified Flask Server**: Handles both VTT ingestion and chat proxying

### Updated Data Flow
```
YouTube Video → Chrome Extension → Flask Server → Direct RAG Agent → AI Response
                     ↓                    ↓              ↓
              User Interface      yt-dlp + chunking   Vector Search
                                                      + Chat Memory
```

### Implementation Steps
1. ✅ Create `youtube_transcript_pages` table in Supabase
2. Implement VTT chunking function in Flask server
3. Add OpenAI embedding generation
4. Create database insertion functions
5. Build RAG agent with database query capabilities
6. Update Flask endpoints to use direct RAG instead of n8n
7. Maintain Chrome extension integration

### Database Schema Design Decisions

**Dual Identifier Strategy:**
- **video_id column**: YouTube ID for efficient filtering and indexing (unconstrained for future-proofing)
- **url column**: Full YouTube URL for debugging, links, and flexibility
- **Rationale**: video_id enables fast queries while url provides human-readable context

**Indexing Strategy:**
- **Vector index**: ivfflat for semantic similarity search performance
- **video_id index**: B-tree for fast video-specific filtering 
- **Metadata GIN index**: Flexible JSONB filtering for timestamps and other attributes

**Unique Constraint:**
- Changed from `(url, chunk_number)` to `(video_id, chunk_number)`
- Prevents duplicate chunks per video while allowing same video from different URL formats

### Benefits of Direct Approach
- **Better chunking control** - Custom logic for optimal semantic boundaries
- **Simplified architecture** - Removes n8n dependency
- **Faster iteration** - Direct Python development vs workflow debugging
- **Enhanced debugging** - Full visibility into chunking and retrieval process

## Status: 🔄 Transitioning to Direct RAG

Current system functional, planning migration to:
- ✅ Chrome extension integration (maintained)
- 🔄 Direct Python-based RAG system (in progress)
- 🔄 Custom chunking implementation
- 🔄 Simplified Flask server architecture

Last updated: July 26, 2025