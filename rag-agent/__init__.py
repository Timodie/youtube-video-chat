# RAG Agent Package for YouTube Transcript Processing
"""
This package contains the RAG (Retrieval Augmented Generation) agent for processing
YouTube transcripts and enabling AI-powered chat functionality.

Main components:
- rag_agent: Core AI agent with chat capabilities
- ingest_youtube: Transcript processing and vector storage
"""

# Make key components available at package level
try:
    from .rag_agent import youtube_ai_assistant, PydanticAIDeps
    from .ingest_youtube import process_and_store_transcript
    
    __all__ = [
        'youtube_ai_assistant',
        'PydanticAIDeps', 
        'process_and_store_transcript'
    ]
except ImportError as e:
    print(f"Warning: Could not import RAG components: {e}")
    __all__ = []