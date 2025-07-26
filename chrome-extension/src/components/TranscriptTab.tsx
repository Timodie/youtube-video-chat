import React, { useEffect } from 'react';
import { useTranscript } from '../hooks/useTranscript';
import { useChat } from '../hooks/useChat';

export default function TranscriptTab({ videoId }) {
  const { transcript, loading, error, fetchTranscript } = useTranscript();
  const { chatStatus, startPolling } = useChat(videoId);

  useEffect(() => {
    if (videoId) {
      const videoUrl = window.location.href;
      fetchTranscript(videoUrl).then((data) => {
        // Start polling if RAG processing not complete
        if (data && !data.rag_stored) {
          startPolling();
        }
      }).catch(console.error);
    }
  }, [videoId, fetchTranscript, startPolling]);

  const handleTimestampClick = (seconds) => {
    const video = document.querySelector('video');
    if (video) {
      video.currentTime = seconds;
      video.play();
    }
  };

  if (loading) {
    return (
      <div className="tab-content active">
        <div className="loading-state">
          <div className="spinner"></div>
          <h4>Getting Transcript...</h4>
          <p>Please wait while we extract the transcript from this video.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tab-content active">
        <div className="error-state">
          <div className="icon">❌</div>
          <h4>Error</h4>
          <p>{error}</p>
          <button className="retry-btn" onClick={() => fetchTranscript(window.location.href)}>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!transcript) {
    return (
      <div className="tab-content active">
        <div className="loading-state">
          <h4>No transcript loaded</h4>
          <p>Click the "Get Transcript" button to extract the transcript.</p>
        </div>
      </div>
    );
  }

  // Status display for optimized architecture
  const cacheStatus = transcript.cached ? '🚀 Cached' : '🆕 Fresh';
  const ragStatus = transcript.rag_stored ? '✅ Chat Ready' : '⏳ Processing...';
  const extractionTime = transcript.extraction_time ? ` (${transcript.extraction_time.toFixed(1)}s)` : '';
  const storageStatus = `${cacheStatus}${extractionTime} | ${ragStatus}`;

  return (
    <div className="tab-content active">
      <div className="transcript-header">
        <h4>{transcript.title}</h4>
        <p className="video-info">
          Language: {transcript.language} ({transcript.language_code}) | {storageStatus}
        </p>
      </div>
      
      <div className="transcript-list">
        {transcript.transcript.map((item, index) => (
          <div 
            key={index}
            className="transcript-item" 
            onClick={() => handleTimestampClick(item.start_seconds)}
          >
            <div className="timestamp">{item.start}</div>
            <div className="transcript-text">{item.text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}