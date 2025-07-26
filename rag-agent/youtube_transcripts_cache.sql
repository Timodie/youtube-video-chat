-- YouTube Transcripts Caching Table
-- This table stores raw transcript data for fast lookups and prevents re-extraction

create table youtube_transcripts_cache (
  video_id varchar primary key,
  url varchar not null,
  title varchar not null,
  language varchar default 'English',
  language_code varchar default 'en',
  transcript_data jsonb not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create index on url for debugging and alternative lookups
create index idx_youtube_transcripts_cache_url on youtube_transcripts_cache(url);

-- Create index on created_at for cleanup queries
create index idx_youtube_transcripts_cache_created_at on youtube_transcripts_cache(created_at);

-- Add comments for documentation
comment on table youtube_transcripts_cache is 'Caches YouTube transcript data to avoid re-extraction with yt-dlp';
comment on column youtube_transcripts_cache.video_id is 'YouTube video ID (primary key)';
comment on column youtube_transcripts_cache.url is 'Full YouTube URL for reference';
comment on column youtube_transcripts_cache.title is 'Video title extracted from YouTube';
comment on column youtube_transcripts_cache.transcript_data is 'Raw VTT transcript data as JSONB array';
comment on column youtube_transcripts_cache.created_at is 'When transcript was first extracted';

-- Example of stored transcript_data structure:
-- [
--   {
--     "start": "00:00:00.000",
--     "end": "00:00:03.000", 
--     "text": "We're no strangers to love",
--     "start_seconds": 0.0,
--     "end_seconds": 3.0
--   },
--   ...
-- ]