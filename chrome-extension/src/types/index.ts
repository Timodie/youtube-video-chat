// API Response Types
export interface TranscriptEntry {
  start: string;
  end: string;
  text: string;
  start_seconds: number;
  end_seconds: number;
}

export interface TranscriptResponse {
  success: boolean;
  video_id: string;
  title: string;
  url: string;
  language: string;
  language_code: string;
  transcript: TranscriptEntry[];
  rag_stored: boolean;
  cached: boolean;
  extraction_time: number;
  error?: string;
}

export interface ChatStatusResponse {
  available: boolean;
  status: 'ready' | 'processing' | 'not_found' | 'error' | 'rag_unavailable';
  chunk_count: number;
  message: string;
  video_id: string;
  retry_after?: number;
  error?: string;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  chat_history: ChatMessage[];  // NEW: Full conversation history
  timestamps: string[];
  video_id: string;
  session_id: string;           // NEW: Session tracking
  method?: string;
  processed_at?: string;
  error?: string;
}

export interface ChatRequest {
  chatInput: string;
  video_id: string;
  sessionId: string;
}

// Chat Message Types (API format)
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  message: string;
  timestamp: string;
}

// UI Chat Message Types (for display)
export interface UIChatMessage {
  id: string;
  type: 'user' | 'ai' | 'system' | 'loading';
  content: string;
  timestamps?: string[];
  timestamp: Date;
}

// Hook State Types
export interface TranscriptState {
  transcript: TranscriptResponse | null;
  loading: boolean;
  error: string | null;
}

export interface ChatState {
  messages: UIChatMessage[];  // Use UI format for existing state
  chatStatus: ChatStatusResponse | null;
  loading: boolean;
  polling: boolean;
}

// Component Props Types
export interface SidebarProps {
  videoId: string | null;
  onClose: () => void;
}

export interface TranscriptTabProps {
  videoId: string | null;
}

export interface ChatTabProps {
  videoId: string | null;
  chatHistory: ChatMessage[];
  onChatUpdate: (newChatHistory: ChatMessage[]) => void;
  isLoading: boolean;
}

export interface TranscriptButtonProps {
  onClick: () => void;
  videoId: string | null;
}

export interface ChatMessageProps {
  message: UIChatMessage;
}

// API Error Types
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}