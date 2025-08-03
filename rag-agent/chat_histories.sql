-- Chat Histories Table for YouTube Video Conversations
-- Supports conversation memory with smart summarization

CREATE TABLE chat_histories (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  video_id text NOT NULL,
  session_id text NOT NULL,
  role text NOT NULL CHECK (role IN ('user', 'assistant', 'summary')),
  message text NOT NULL,
  timestamp timestamp DEFAULT now(),
  summarizes_from_id uuid, -- Points to first message this summary covers (only used when role = 'summary')
  summarizes_to_id uuid,   -- Points to last message this summary covers (only used when role = 'summary')
  created_at timestamp DEFAULT now()
);

-- Index for fast retrieval by video/session ordered by time
CREATE INDEX idx_chat_histories_session 
ON chat_histories (video_id, session_id, timestamp);

-- Index for summary range queries (finding existing summaries)
CREATE INDEX idx_chat_histories_summary_range 
ON chat_histories (video_id, session_id, summarizes_from_id, summarizes_to_id) 
WHERE role = 'summary';

-- Index for efficient filtering of display messages (user/assistant only)
CREATE INDEX idx_chat_histories_display 
ON chat_histories (video_id, session_id, timestamp) 
WHERE role IN ('user', 'assistant');

-- Add RLS (Row Level Security) policies if needed
-- ALTER TABLE chat_histories ENABLE ROW LEVEL SECURITY;

-- Example usage comments:
-- 
-- Store user message:
-- INSERT INTO chat_histories (video_id, session_id, role, message) 
-- VALUES ('dQw4w9WgXcQ', 'dQw4w9WgXcQ', 'user', 'What is this video about?');
--
-- Store AI response:
-- INSERT INTO chat_histories (video_id, session_id, role, message) 
-- VALUES ('dQw4w9WgXcQ', 'dQw4w9WgXcQ', 'assistant', 'This video is about...');
--
-- Store conversation summary:
-- INSERT INTO chat_histories (video_id, session_id, role, message, summarizes_from_id, summarizes_to_id) 
-- VALUES ('dQw4w9WgXcQ', 'dQw4w9WgXcQ', 'summary', 'User asked about video content...', 'uuid1', 'uuid2');
--
-- Get all messages for display (excludes summaries):
-- SELECT id, role, message, timestamp FROM chat_histories 
-- WHERE video_id = 'dQw4w9WgXcQ' AND session_id = 'dQw4w9WgXcQ' AND role IN ('user', 'assistant')
-- ORDER BY timestamp;
--
-- Check for existing summary covering a range:
-- SELECT message FROM chat_histories 
-- WHERE video_id = 'dQw4w9WgXcQ' AND session_id = 'dQw4w9WgXcQ' 
-- AND role = 'summary' AND summarizes_from_id = 'uuid1' AND summarizes_to_id = 'uuid2';