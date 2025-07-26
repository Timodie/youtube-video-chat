import React from 'react';

export default function TranscriptButton({ onClick, videoId }) {
  if (!videoId) {
    return null;
  }

  return (
    <div className="transcript-btn-container">
      <button 
        className="transcript-btn" 
        onClick={onClick}
        id="transcript-extractor-btn"
      >
        📝 Get Transcript
      </button>
    </div>
  );
}