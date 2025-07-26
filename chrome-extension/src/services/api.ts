import { TranscriptResponse, ChatStatusResponse, ChatResponse, APIError } from '../types';

const API_BASE_URL = 'http://localhost:8080';

export class YouTubeTranscriptAPI {
  /**
   * Extract transcript for a YouTube video
   */
  static async getTranscript(url: string): Promise<TranscriptResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/transcript`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url })
      });

      const data: TranscriptResponse = await response.json();
      
      if (!data.success) {
        throw new APIError(data.error || 'Failed to get transcript', response.status, data);
      }

      return data;
    } catch (error) {
      console.error('Error fetching transcript:', error);
      if (error instanceof APIError) throw error;
      throw new APIError('Network error while fetching transcript');
    }
  }

  /**
   * Check if chat is available for a video
   */
  static async getChatStatus(videoId: string): Promise<ChatStatusResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/status/${videoId}`);
      
      if (!response.ok) {
        throw new APIError(`HTTP ${response.status}`, response.status);
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking chat status:', error);
      if (error instanceof APIError) throw error;
      throw new APIError('Network error while checking chat status');
    }
  }

  /**
   * Send chat message about a video
   */
  static async sendChatMessage(videoId: string, message: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          chatInput: message,
          video_id: videoId,
          sessionId: videoId
        })
      });

      const data: ChatResponse = await response.json();
      
      if (!data.success) {
        throw new APIError(data.error || 'Chat request failed', response.status, data);
      }

      return data;
    } catch (error) {
      console.error('Error sending chat message:', error);
      if (error instanceof APIError) throw error;
      throw new APIError('Network error while sending chat message');
    }
  }
}

/**
 * Extract video ID from YouTube URL
 */
export function extractVideoId(url: string): string | null {
  const patterns = [
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
    /youtube\.com\/watch\?.*v=([^&\n?#]+)/
  ];
  
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  
  return null;
}

/**
 * Get current video ID from page URL
 */
export function getCurrentVideoId(): string | null {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('v');
}