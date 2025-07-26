-- Enable the pgvector extension
create extension if not exists vector;

-- Create the documentation chunks table, changes this to youtube_pages
create table youtube_transcript_pages (
    id bigserial primary key,
    video_id varchar not null,  -- YouTube video ID for efficient filtering
    url varchar not null,  -- Keep full URL for links and debugging
    chunk_number integer not null,
    title varchar not null,
    summary varchar not null,
    content text not null,  -- Added content column
    metadata jsonb not null default '{}'::jsonb,  -- Added metadata column
    embedding vector(1536),  -- OpenAI embeddings are 1536 dimensions
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,

    -- Add a unique constraint to prevent duplicate chunks for the same video
    unique(video_id, chunk_number)
);

-- Create an index for better vector similarity search performance
create index on youtube_transcript_pages using ivfflat (embedding vector_cosine_ops);

-- Create an index on video_id for faster filtering by video
create index idx_youtube_transcript_pages_video_id on youtube_transcript_pages (video_id);

-- Create an index on metadata for faster filtering
create index idx_youtube_transcript_pages_metadata on youtube_transcript_pages using gin (metadata);

-- Create a function to search for documentation chunks
create function match_youtube_transcript_pages (
  query_embedding vector(1536),
  match_count int default 10,
  filter jsonb DEFAULT '{}'::jsonb
) returns table (
  id bigint,
  video_id varchar,
  url varchar,
  chunk_number integer,
  title varchar,
  summary varchar,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
#variable_conflict use_column
begin
  return query
  select
    id,
    video_id,
    url,
    chunk_number,
    title,
    summary,
    content,
    metadata,
    1 - (youtube_transcript_pages.embedding <=> query_embedding) as similarity
  from youtube_transcript_pages
  where metadata @> filter
  order by youtube_transcript_pages.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Everything above will work for any PostgreSQL database. The below commands are for Supabase security

-- Enable RLS on the table
alter table youtube_transcript_pages enable row level security;

-- Create a policy that allows anyone to read
create policy "Allow public read access"
  on youtube_transcript_pages
  for select
  to public
  using (true);
