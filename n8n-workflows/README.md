# n8n Workflows

This directory contains n8n workflow configurations for the YouTube Video Chat project.

## Files

- `original-document-workflow.json` - Your existing document processing workflow (paste here)
- `youtube-video-workflow.json` - Adapted workflow for YouTube transcripts (will be generated)

## Usage

1. **Export your current n8n workflow**: 
   - Go to your n8n dashboard
   - Select your document processing workflow
   - Click Export → Download as JSON
   - Save the file as `original-document-workflow.json` in this directory

2. **Import the YouTube workflow**:
   - After the adapted workflow is created, import `youtube-video-workflow.json` into your n8n instance
   - Configure the credentials and connection settings
   - Test with a sample YouTube transcript

## Workflow Differences

The YouTube workflow will be adapted from your document workflow with these key changes:

- **Trigger**: Webhook from Flask server instead of Google Drive
- **Input**: Video transcript with metadata instead of document text
- **Chunking**: Timestamp-aware chunking for video content
- **Storage**: Video ID namespacing in Supabase
- **Agent Prompts**: Video-specific context and instructions
- **Cleanup**: Optional cleanup logic for old video transcripts