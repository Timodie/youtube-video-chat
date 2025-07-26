import { useState, useCallback } from 'react';
import { YouTubeTranscriptAPI } from '../services/api';
import { TranscriptResponse, APIError } from '../types';

interface UseTranscriptReturn {
  transcript: TranscriptResponse | null;
  loading: boolean;
  error: string | null;
  fetchTranscript: (videoUrl: string) => Promise<TranscriptResponse | undefined>;
  clearTranscript: () => void;
}

/**
 * Hook for managing transcript state and operations
 */
export function useTranscript(): UseTranscriptReturn {
  const [transcript, setTranscript] = useState<TranscriptResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTranscript = useCallback(async (videoUrl: string): Promise<TranscriptResponse | undefined> => {
    if (!videoUrl) {
      setError('No video URL provided');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await YouTubeTranscriptAPI.getTranscript(videoUrl);
      setTranscript(data);
      return data;
    } catch (err) {
      const errorMessage = err instanceof APIError ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      setTranscript(null);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearTranscript = useCallback((): void => {
    setTranscript(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    transcript,
    loading,
    error,
    fetchTranscript,
    clearTranscript
  };
}