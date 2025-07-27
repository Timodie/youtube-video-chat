import { useState } from 'react';
import TranscriptTab from './TranscriptTab';
import ChatTab from './ChatTab';
import { SidebarProps } from '../types';

type TabType = 'transcript' | 'chat';

export default function Sidebar({ videoId, onClose }: SidebarProps): JSX.Element {
  const [activeTab, setActiveTab] = useState<TabType>('transcript');

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
          <ChatTab videoId={videoId} />
        )}
      </div>
    </div>
  );
}