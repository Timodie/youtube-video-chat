import { useState, useEffect } from 'react';
import TranscriptTab from './TranscriptTab';
import ChatTab from './ChatTab';
import { SidebarProps, ChatMessage } from '../types';
import { YouTubeTranscriptAPI } from '../services/api';

type TabType = 'transcript' | 'chat';

export default function Sidebar({ videoId, onClose }: SidebarProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('transcript');
  
  // Chat state moved to Sidebar level for persistence across tab switches
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatInitialized, setChatInitialized] = useState(false);

  // Load chat history when sidebar opens or video changes
  useEffect(() => {
    if (videoId && !chatInitialized) {
      loadChatHistory();
    }
  }, [videoId, chatInitialized]);

  const loadChatHistory = async () => {
    if (!videoId) return;
    
    try {
      setChatLoading(true);
      const response = await YouTubeTranscriptAPI.getChatHistory(videoId);
      
      if (response.success) {
        setChatHistory(response.chat_history);
        console.log(`📚 Loaded ${response.message_count} previous messages for ${videoId}`);
      } else {
        console.warn('Failed to load chat history:', response.error);
        setChatHistory([]);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
      setChatHistory([]); // Start fresh on error
    } finally {
      setChatLoading(false);
      setChatInitialized(true);
    }
  };

  const handleChatUpdate = (newChatHistory: ChatMessage[]) => {
    setChatHistory(newChatHistory);
  };

  return (
    <div className="transcript-sidebar open">
      <div className="sidebar-header">
        <h3>📝 Video Assistant</h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>
      
      <div className="sidebar-tabs">
        <button 
          className={`tab-btn ${activeTab === 'transcript' ? 'active' : ''}`}
          onClick={() => setActiveTab('transcript')}
        >
          📝 Transcript
        </button>
        <button 
          className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          💬 Chat
        </button>
      </div>
      
      <div className="sidebar-content">
        {activeTab === 'transcript' && (
          <TranscriptTab videoId={videoId} />
        )}
        {activeTab === 'chat' && (
          <ChatTab 
            videoId={videoId}
            chatHistory={chatHistory}
            onChatUpdate={handleChatUpdate}
            isLoading={chatLoading}
          />
        )}
      </div>
    </div>
  );
}