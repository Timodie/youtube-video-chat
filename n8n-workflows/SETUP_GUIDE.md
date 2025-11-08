# YouTube Voice Agent + ElevenLabs + Supabase Setup Guide

## Overview
This workflow connects your existing YouTube transcript RAG system to ElevenLabs voice agents, enabling natural voice conversations about YouTube videos.

## Prerequisites
- n8n instance (cloud or self-hosted)
- ElevenLabs account with Conversational AI access
- Supabase project with your existing YouTube transcript data
- OpenAI API key

## Step 1: Import n8n Workflow

1. Open your n8n instance
2. Click "Import workflow" 
3. Upload `youtube-voice-agent-workflow.json`
4. The workflow will be imported with all nodes configured

## Step 2: Configure Credentials

### Supabase Credentials
1. In n8n, go to Settings > Credentials
2. Add new "Supabase" credential:
   - **Host**: Your Supabase project URL (e.g., `https://your-project.supabase.co`)
   - **Service Role Secret**: Your Supabase service role key (from Project Settings > API)

### PostgreSQL Credentials (for direct vector search)
1. Add new "Postgres" credential:
   - **Host**: `db.your-project.supabase.co`
   - **Database**: `postgres`  
   - **User**: `postgres`
   - **Password**: Your database password
   - **Port**: `5432`
   - **SSL**: Enable

### OpenAI Credentials  
1. Add new "OpenAI" credential:
   - **API Key**: Your OpenAI API key

## Step 3: Configure ElevenLabs Voice Agent

### Create Voice Agent
1. Log into ElevenLabs platform
2. Go to Conversational AI > Agents
3. Create new agent with these settings:
   - **Name**: YouTube Video Assistant
   - **Voice**: Choose preferred voice
   - **First Message**: "Hi! I can help you understand any YouTube video. Just ask me questions about the content!"

### System Prompt for ElevenLabs Agent:
```
You are a YouTube video assistant. Users will ask you questions about specific YouTube videos they're watching. 

When a user asks a question:
1. Use the knowledge_base tool to send their question to the n8n webhook
2. Include the video_id if they mention it, or ask them for it if unclear
3. Wait for the response and share it naturally in conversation
4. Keep responses conversational and under 2 minutes when speaking

You have access to detailed video transcripts and can provide specific timestamps for navigation.
```

### Add Knowledge Base Tool
1. In your ElevenLabs agent, add a **Knowledge Base** tool
2. Configure the tool:
   - **Name**: `youtube_transcript_search`
   - **Description**: "Search YouTube video transcripts and chat with AI about video content"
   - **Webhook URL**: `https://your-n8n-instance.com/webhook/youtube-voice-chat`
   - **Method**: POST
   - **Parameters**:
     ```json
     {
       "question": "{{ user_input }}",
       "video_id": "{{ video_id }}",
       "session_id": "{{ conversation_id }}"
     }
     ```

## Step 4: Test the Integration

### Test Data Setup
Make sure you have test data in your Supabase tables:

```sql
-- Check if you have transcript data
SELECT video_id, title, COUNT(*) as chunk_count 
FROM youtube_transcript_pages 
GROUP BY video_id, title 
LIMIT 5;

-- Sample video_id for testing: Use one from your actual data
```

### Test the Webhook Directly
```bash
curl -X POST "https://your-n8n-instance.com/webhook/youtube-voice-chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this video about?",
    "video_id": "your-actual-video-id",
    "session_id": "test-session-123"
  }'
```

Expected response:
```json
{
  "response": "This video discusses...",
  "timestamps": ["00:02:30", "00:05:45"],
  "success": true,
  "video_id": "your-video-id",
  "context_chunks": 5,
  "conversation_length": 2
}
```

### Test with ElevenLabs
1. Start a conversation with your ElevenLabs agent
2. Say: "Tell me about video [your-video-id]"
3. Ask follow-up questions like "What happens at the beginning?"
4. Test conversation memory with "What did you just tell me about?"

## Step 5: Advanced Configuration

### Voice Optimization Settings

In the n8n workflow, you can adjust these parameters:

**AI Response Node (Generate AI Response):**
- `temperature`: 0.7 (conversational but focused)
- `maxTokens`: 300 (keeps responses concise for voice)

**Vector Search:**
- `LIMIT 5`: Returns top 5 relevant chunks (adjust based on video length)

**Chat History:**
- `LIMIT 10`: Keeps last 10 conversation turns (adjust for memory length)

### Error Handling

The workflow includes automatic error handling for:
- Videos without transcript data
- Invalid video IDs  
- Empty search results
- API failures

### Performance Optimization

**For High Usage:**
1. Add rate limiting in n8n
2. Implement caching for frequent questions
3. Use batch processing for multiple requests

**Cost Management:**
- Each conversation turn costs ~$0.002-0.005 in OpenAI API calls
- Embedding generation is cached in your existing system
- Chat memory uses efficient summarization (as per your existing design)

## Step 6: Production Deployment

### Security
1. Enable webhook authentication in n8n
2. Use HTTPS for all endpoints
3. Set up proper CORS headers
4. Monitor API usage and costs

### Monitoring
1. Set up n8n execution logging
2. Monitor Supabase database performance
3. Track OpenAI API usage
4. Monitor ElevenLabs voice generation costs

### Scaling
- Use n8n Cloud for automatic scaling
- Consider Redis for caching frequent queries
- Implement connection pooling for Supabase

## Workflow Features

✅ **Voice-Optimized Responses**: Formatted for natural speech patterns
✅ **Conversation Memory**: Maintains context across voice interactions  
✅ **Timestamp Integration**: Provides specific video navigation points
✅ **Error Handling**: Graceful fallbacks for missing data
✅ **Cost Efficient**: Uses existing embeddings and smart context building
✅ **Session Isolation**: Separate conversations per user/video
✅ **Real-time Processing**: Responds quickly to voice queries

## Troubleshooting

### Common Issues

**"No transcript data found":**
- Verify video was processed by your Chrome extension
- Check Supabase `youtube_transcript_pages` table has data for the video_id

**Webhook not responding:**
- Check n8n workflow is active
- Verify webhook URL in ElevenLabs matches n8n
- Check n8n execution logs for errors

**Poor voice responses:**
- Adjust OpenAI temperature (lower = more focused)
- Modify system prompt for better voice optimization
- Check maxTokens setting (too high = long responses)

**Memory not working:**
- Verify `chat_histories` table exists and has proper indexes
- Check session_id is being passed consistently
- Review chat history retrieval query

### Support
For issues specific to:
- **n8n**: Check n8n community forum
- **ElevenLabs**: Contact ElevenLabs support
- **Supabase**: Check Supabase documentation
- **This workflow**: Create an issue in your repository

## Next Steps
- Add multi-language support
- Implement voice commands for video navigation  
- Add sentiment analysis for conversation insights
- Create dashboard for usage analytics