import { useState, useRef, useEffect } from 'react';
import { ChatTabProps, ChatMessage } from '../types';
import { SafeMarkdown } from './SafeMarkdown';
import { YouTubeTranscriptAPI } from '../services/api';

export default function ChatTab({ 
  videoId, 
  chatHistory, 
  onChatUpdate, 
  isLoading: parentLoading 
}: ChatTabProps): JSX.Element {
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const sendMessage = async (message: string) => {
    if (!message.trim() || isSending || !videoId) return;
    
    // TODO: Optimize state management to avoid full chat_history replacement
    // Current approach: Optimistic UI + full state replacement from API
    // Future: Implement incremental updates to avoid re-rendering entire conversation
    // This would require backend changes to return only new messages
    
    // STEP 1: Optimistic update - show user message immediately
    const optimisticUserMessage: ChatMessage = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      message: message.trim(),
      timestamp: new Date().toISOString()
    };
    
    onChatUpdate([...chatHistory, optimisticUserMessage]);
    setInputValue('');
    setIsSending(true);
    
    try {
      // STEP 2: Show AI typing indicator
      const typingMessage: ChatMessage = {
        id: 'typing-indicator',
        role: 'assistant', 
        message: '...',  // Special message that renders as typing dots
        timestamp: new Date().toISOString()
      };
      onChatUpdate([...chatHistory, optimisticUserMessage, typingMessage]);
      
      // STEP 3: Send to API
      const response = await YouTubeTranscriptAPI.sendChatMessage(videoId, message);
      
      if (response.success) {
        // STEP 4: Replace with authoritative chat history from API
        // TODO: This causes full re-render of conversation - optimize later
        onChatUpdate(response.chat_history);
      } else {
        // Error: Remove optimistic messages, show error
        onChatUpdate(chatHistory); // Revert to original state
        // TODO: Show error toast/notification to user
        console.error('Chat error:', response.error);
      }
      
    } catch (error) {
      // Network error: Remove optimistic messages  
      onChatUpdate(chatHistory); // Revert to original state
      console.error('Failed to send message:', error);
      // TODO: Show error toast/notification to user
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  return (
    <div className="tab-content active" id="chat-tab">
      <div className="chat-messages">
        {parentLoading ? (
          <div className="loading-history">
            <div className="spinner"></div>
            <p>Loading conversation...</p>
          </div>
        ) : (
          <>
            {chatHistory.length === 0 ? (
              <div className="welcome-message">
                <p>👋 Ask me anything about this video!</p>
                <p><em>I can provide timestamps and quotes from the transcript.</em></p>
              </div>
            ) : (
              chatHistory.map((msg, index) => {
                // Special handling for typing indicator
                if (msg.id === 'typing-indicator') {
                  return (
                    <div key="typing" className="ai-message">
                      <div className="message-avatar">🤖</div>
                      <div className="loading-content">
                        <div className="typing-indicator">
                          <div className="typing-dot"></div>
                          <div className="typing-dot"></div>
                          <div className="typing-dot"></div>
                        </div>
                      </div>
                    </div>
                  );
                }
                
                // Regular message rendering
                return (
                  <div 
                    key={msg.id || index} 
                    className={`${msg.role}-message ${
                      msg.id?.startsWith('temp-') ? 'optimistic' : ''
                    }`}
                  >
                    <div className="message-avatar">
                      {msg.role === 'user' ? '👤' : '🤖'}
                    </div>
                    <div className="message-content">
                      <SafeMarkdown content={msg.message} />
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      <div className="chat-input-container">
        <form onSubmit={handleSubmit}>
          <input
            id="chat-input"
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about this video..."
            disabled={isSending || parentLoading}
          />
          <button
            id="send-btn"
            type="submit"
            disabled={!inputValue.trim() || isSending || parentLoading}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

