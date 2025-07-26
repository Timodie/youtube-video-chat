import { useState, useCallback, useEffect, useRef } from 'react';
import { YouTubeTranscriptAPI } from '../services/api';
import { ChatMessage, ChatStatusResponse, APIError } from '../types';

interface UseChatReturn {
  messages: ChatMessage[];
  chatStatus: ChatStatusResponse | null;
  loading: boolean;
  polling: boolean;
  sendMessage: (message: string) => Promise<void>;
  checkChatStatus: () => Promise<ChatStatusResponse | null>;
  startPolling: () => void;
  stopPolling: () => void;
}

/**
 * Hook for managing chat state and operations
 */
export function useChat(videoId: string | null): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatStatus, setChatStatus] = useState<ChatStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [polling, setPolling] = useState<boolean>(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  // Welcome message
  useEffect(() => {
    setMessages([{
      id: 'welcome',
      type: 'ai',
      content: "Hi! I'm your video assistant. I can help you chat about this video's content. Ask me anything about what you're watching!",
      timestamp: new Date()
    }]);
  }, []);

  // Check chat status
  const checkChatStatus = useCallback(async (): Promise<ChatStatusResponse | null> => {
    if (!videoId) return null;

    try {
      const status = await YouTubeTranscriptAPI.getChatStatus(videoId);
      setChatStatus(status);
      return status;
    } catch (error) {
      const errorStatus: ChatStatusResponse = {
        available: false,
        status: 'error',
        chunk_count: 0,
        message: 'Could not check chat status. Server may be offline.',
        video_id: videoId
      };
      setChatStatus(errorStatus);
      return null;
    }
  }, [videoId]);

  // Start status polling
  const startPolling = useCallback((): void => {
    if (pollingRef.current || !videoId) return;

    setPolling(true);
    pollingRef.current = setInterval(async () => {
      const status = await checkChatStatus();
      
      if (status && status.available && status.status === 'ready') {
        // Chat is ready, stop polling
        setPolling(false);
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
        
        // Add system message about chat being ready
        setMessages(prev => [...prev, {
          id: `chat-ready-${Date.now()}`,
          type: 'system',
          content: '🎉 Chat is now ready! You can ask questions about this video.',
          timestamp: new Date()
        }]);
      }
    }, 15000); // Poll every 15 seconds

    // Auto-stop polling after 10 minutes
    setTimeout(() => {
      if (pollingRef.current) {
        setPolling(false);
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }, 600000);
  }, [videoId, checkChatStatus]);

  // Stop status polling
  const stopPolling = useCallback((): void => {
    if (pollingRef.current) {
      setPolling(false);
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  // Send chat message
  const sendMessage = useCallback(async (message: string): Promise<void> => {
    if (!message.trim() || !videoId) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: message,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Add loading message
    const loadingMessage: ChatMessage = {
      id: `loading-${Date.now()}`,
      type: 'loading',
      content: '',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, loadingMessage]);

    setLoading(true);

    try {
      const response = await YouTubeTranscriptAPI.sendChatMessage(videoId, message);
      
      // Remove loading message and add AI response
      setMessages(prev => [
        ...prev.filter(msg => msg.id !== loadingMessage.id),
        {
          id: `ai-${Date.now()}`,
          type: 'ai',
          content: response.response,
          timestamps: response.timestamps || [],
          timestamp: new Date()
        }
      ]);
    } catch (error) {
      const errorMessage = error instanceof APIError ? error.message : 'Unknown error occurred';
      
      // Remove loading message and add error message
      setMessages(prev => [
        ...prev.filter(msg => msg.id !== loadingMessage.id),
        {
          id: `error-${Date.now()}`,
          type: 'ai',
          content: `Error: ${errorMessage}`,
          timestamp: new Date()
        }
      ]);
    } finally {
      setLoading(false);
    }
  }, [videoId]);

  // Clear chat when video changes
  useEffect(() => {
    if (videoId) {
      setMessages([{
        id: 'welcome',
        type: 'ai',
        content: "Hi! I'm your video assistant. I can help you chat about this video's content. Ask me anything about what you're watching!",
        timestamp: new Date()
      }]);
      setChatStatus(null);
      stopPolling();
      checkChatStatus();
    }
  }, [videoId, checkChatStatus, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    messages,
    chatStatus,
    loading,
    polling,
    sendMessage,
    checkChatStatus,
    startPolling,
    stopPolling
  };
}