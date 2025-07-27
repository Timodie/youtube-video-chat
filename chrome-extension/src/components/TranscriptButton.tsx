// No React import needed for modern React with JSX transform
import { TranscriptButtonProps } from '../types';

export default function TranscriptButton({ onClick, videoId }: TranscriptButtonProps): JSX.Element | null {
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