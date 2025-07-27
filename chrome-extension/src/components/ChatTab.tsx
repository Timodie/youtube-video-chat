import { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import { ChatTabProps, ChatMessageProps } from '../types';
import { SafeMarkdown } from './SafeMarkdown';

export default function ChatTab({ videoId }: ChatTabProps): JSX.Element {
  const [inputMessage, setInputMessage] = useState('');
  const { 
    messages, 
    chatStatus, 
    loading, 
    polling, 
    sendMessage, 
    checkChatStatus
  } = useChat(videoId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check chat status on mount
  useEffect(() => {
    if (videoId) {
      checkChatStatus();
    }
  }, [videoId, checkChatStatus]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    await sendMessage(inputMessage);
    setInputMessage('');
  };

  const handleRetryStatus = () => {
    checkChatStatus();
  };

  const isChatAvailable = chatStatus?.available && chatStatus?.status === 'ready';
  const isProcessing = chatStatus?.status === 'processing';

  return (
    <div className="tab-content active" id="chat-tab">
      <div className="chat-messages" id="chat-messages">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        
        {/* Status messages */}
        {isProcessing && !polling && (
          <div className="chat-message system">
            <div className="chat-content">
              <p>🔄 {chatStatus.message || 'Transcript is being processed for AI chat.'}</p>
              <button 
                onClick={handleRetryStatus}
                className="retry-chat-btn"
              >
                🔄 Check Chat Status
              </button>
            </div>
          </div>
        )}
        
        {polling && (
          <div className="chat-message system">
            <div className="chat-content">
              <p>⏳ Checking chat status automatically...</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="chat-input-container">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder={
            isChatAvailable 
              ? "Ask about this video..." 
              : isProcessing 
                ? "⏳ Processing transcript for AI chat..."
                : "❌ Video not found. Extract transcript first."
          }
          disabled={!isChatAvailable || loading}
          id="chat-input"
        />
        <button 
          type="submit" 
          disabled={!isChatAvailable || loading || !inputMessage.trim()}
          id="send-btn"
        >
          Send
        </button>
      </form>
    </div>
  );
}

function ChatMessage({ message }: ChatMessageProps) {
  if (message.type === 'loading') {
    return (
      <div className="chat-message ai loading-message">
        <div className="message-avatar">🤖</div>
        <div className="message-content loading-content">
          <div className="typing-indicator">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        </div>
      </div>
    );
  }

  if (message.type === 'system') {
    return (
      <div className="chat-message system">
        <div className="message-content">
          <p>{message.content}</p>
        </div>
      </div>
    );
  }

  const isUser = message.type === 'user';
  
  return (
    <div className={`chat-message ${isUser ? 'user' : 'ai'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="message-content">
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <SafeMarkdown 
            content={message.content} 
            fallback={message.content}
            timestamps={message.timestamps}
          />
        )}
      </div>
    </div>
  );
}