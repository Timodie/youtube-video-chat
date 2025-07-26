// Content script for YouTube Transcript Extractor
console.log('YouTube Transcript Extractor loaded');

// Function to get current video ID from URL
function getVideoId() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('v');
}

// Function to create sidebar
function createSidebar() {
  const sidebar = document.createElement('div');
  sidebar.id = 'transcript-sidebar';
  sidebar.className = 'transcript-sidebar';
  sidebar.innerHTML = `
    <div class="sidebar-header">
      <h3>📝 Video Assistant</h3>
      <button class="close-btn" id="close-sidebar">×</button>
    </div>
    <div class="sidebar-tabs">
      <button class="tab-btn active" data-tab="transcript">📝 Transcript</button>
      <button class="tab-btn" data-tab="chat">💬 Chat</button>
    </div>
    <div class="sidebar-content" id="sidebar-content">
      <div class="tab-content active" id="transcript-tab">
        <div class="loading-state" id="loading-state">
          <div class="spinner"></div>
          <h4>Getting Transcript...</h4>
          <p>Please wait while we extract the transcript from this video.</p>
        </div>
      </div>
      <div class="tab-content" id="chat-tab">
        <div class="chat-messages" id="chat-messages">
          <div class="welcome-message">
            <div class="ai-message">
              <div class="message-avatar">🤖</div>
              <div class="message-content">
                <p>Hi! I'm your video assistant. I can help you chat about this video's content.</p>
                <p><em>Ask me anything about what you're watching!</em></p>
              </div>
            </div>
          </div>
        </div>
        <div class="chat-input-container">
          <input type="text" id="chat-input" placeholder="Ask about this video..." />
          <button id="send-btn">Send</button>
        </div>
      </div>
    </div>
  `;
  
  // Add event listeners
  sidebar.addEventListener('click', function(e) {
    if (e.target.id === 'close-sidebar') {
      toggleSidebar();
    } else if (e.target.classList.contains('tab-btn')) {
      switchTab(e.target.dataset.tab);
    } else if (e.target.id === 'send-btn') {
      sendChatMessage();
    }
  });
  
  // Add enter key support for chat input
  sidebar.addEventListener('keypress', function(e) {
    if (e.target.id === 'chat-input' && e.key === 'Enter') {
      sendChatMessage();
    }
  });
  
  return sidebar;
}

// Function to switch between tabs
function switchTab(tabName) {
  // Update tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
  
  // Update tab content
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Function to send chat message
async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  
  if (!message) return;
  
  // Get current video ID (prefer stored from transcript, fallback to URL parsing)
  const videoId = window.currentVideoId || getVideoId();
  if (!videoId) {
    addChatMessage('Error: Could not get video ID. Please extract transcript first.', 'ai');
    return;
  }
  
  // Clear input
  input.value = '';
  
  // Add user message
  addChatMessage(message, 'user');
  
  // Add loading bubble
  addLoadingMessage();
  
  try {
    // Send chat message to Flask server
    const response = await fetch('http://localhost:8080/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        chatInput: message,
        video_id: videoId,
        sessionId: videoId  // Use video ID as session ID
      })
    });
    
    const data = await response.json();
    
    // Remove loading message
    removeLoadingMessage();
    
    if (data.success) {
      // Get the response from the server (Flask returns 'response' field)
      const aiResponse = data.response || 'No response from AI';
      
      addChatMessage(aiResponse, 'ai');
      
      // Log additional info for debugging
      console.log('Chat response data:', data);
      if (data.timestamps && data.timestamps.length > 0) {
        console.log('Timestamps found:', data.timestamps);
      }
    } else {
      addChatMessage(`Error: ${data.error || 'Unknown error'}`, 'ai');
    }
    
  } catch (error) {
    console.error('Error sending chat message:', error);
    removeLoadingMessage();
    addChatMessage('Could not connect to chat server. Make sure the Flask server is running on localhost:8080', 'ai');
  }
}

// Function to add chat message
function addChatMessage(message, sender) {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return;
  
  const messageDiv = document.createElement('div');
  messageDiv.className = `chat-message ${sender}`;
  
  if (sender === 'user') {
    messageDiv.innerHTML = `
      <div class="message-avatar">👤</div>
      <div class="message-content">
        <p>${message}</p>
      </div>
    `;
  } else if (sender === 'system') {
    // System messages (status updates, processing info)
    messageDiv.innerHTML = `
      <div class="chat-content">
        <p>${message}</p>
      </div>
    `;
  } else {
    // AI messages
    messageDiv.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-content">
        <p>${message}</p>
      </div>
    `;
  }
  
  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Function to add loading message (iOS-style bubbles)
function addLoadingMessage() {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return;
  
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'chat-message ai loading-message';
  loadingDiv.id = 'loading-chat-message';
  loadingDiv.innerHTML = `
    <div class="message-avatar">🤖</div>
    <div class="message-content loading-content">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  
  chatMessages.appendChild(loadingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Function to remove loading message
function removeLoadingMessage() {
  const loadingMessage = document.getElementById('loading-chat-message');
  if (loadingMessage) {
    loadingMessage.remove();
  }
}

// Function to fetch transcript from Flask server with progressive enhancement
async function fetchTranscript(videoUrl) {
  try {
    // Extract video ID for chat functionality
    const videoId = extractVideoId(videoUrl);
    
    const response = await fetch('http://localhost:8080/transcript', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: videoUrl })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Step 1: Display transcript immediately (whether cached or fresh)
      displayTranscript(data);
      
      // Step 2: Check chat status immediately
      if (videoId) {
        console.log('Checking chat status for video:', videoId);
        await checkChatStatus(videoId);
        
        // Step 3: Start polling if RAG processing not complete
        if (!data.rag_stored) {
          console.log('RAG not ready, starting polling for video:', videoId);
          startChatStatusPolling(videoId);
        }
      } else {
        console.warn('Could not extract video ID from URL:', videoUrl);
        updateChatAvailability({
          available: false,
          status: 'error',
          message: 'Could not extract video ID from URL'
        });
      }
    } else {
      displayError(data.error || 'Failed to get transcript');
    }
  } catch (error) {
    console.error('Error fetching transcript:', error);
    displayError('Could not connect to transcript server. Make sure the Flask server is running on localhost:8080');
  }
}

// Utility function to extract video ID from YouTube URL
function extractVideoId(url) {
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

// Function to display transcript in sidebar
function displayTranscript(data) {
  const transcriptTab = document.getElementById('transcript-tab');
  if (!transcriptTab) return;
  
  // Updated status display for optimized architecture
  const cacheStatus = data.cached ? '🚀 Cached' : '🆕 Fresh';
  const ragStatus = data.rag_stored ? '✅ Chat Ready' : '⏳ Processing...';
  const extractionTime = data.extraction_time ? ` (${data.extraction_time.toFixed(1)}s)` : '';
  const storageStatus = `${cacheStatus}${extractionTime} | ${ragStatus}`;
  
  transcriptTab.innerHTML = `
    <div class="transcript-header">
      <h4>${data.title}</h4>
      <p class="video-info">Language: ${data.language} (${data.language_code}) | ${storageStatus}</p>
    </div>
    <div class="transcript-list" id="transcript-list">
      ${data.transcript.map(item => `
        <div class="transcript-item" data-time="${item.start_seconds}">
          <div class="timestamp">${item.start}</div>
          <div class="transcript-text">${item.text}</div>
        </div>
      `).join('')}
    </div>
  `;
  
  // Store video ID for chat functionality
  window.currentVideoId = data.video_id;
  
  // Add click handlers for transcript items to jump to video time
  const transcriptItems = transcriptTab.querySelectorAll('.transcript-item');
  transcriptItems.forEach(item => {
    item.addEventListener('click', function() {
      const time = parseFloat(this.dataset.time);
      jumpToVideoTime(time);
    });
  });
}

// Function to display error in sidebar
function displayError(errorMessage) {
  const transcriptTab = document.getElementById('transcript-tab');
  if (!transcriptTab) return;
  
  transcriptTab.innerHTML = `
    <div class="error-state">
      <div class="icon">❌</div>
      <h4>Error</h4>
      <p>${errorMessage}</p>
      <button class="retry-btn" onclick="retryTranscript()">Try Again</button>
    </div>
  `;
}

// Function to jump to specific time in video
function jumpToVideoTime(seconds) {
  const video = document.querySelector('video');
  if (video) {
    video.currentTime = seconds;
    video.play();
  }
}

// Function to check chat status for a video
async function checkChatStatus(videoId) {
  try {
    const response = await fetch(`http://localhost:8080/chat/status/${videoId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const status = await response.json();
    console.log('Chat status:', status);
    updateChatAvailability(status);
    return status;
  } catch (error) {
    console.error('Error checking chat status:', error);
    updateChatAvailability({
      available: false,
      status: 'error',
      message: 'Could not check chat status. Server may be offline.'
    });
    return null;
  }
}

// Function to update chat availability based on status
function updateChatAvailability(status) {
  const chatInput = document.getElementById('chat-input');
  const sendButton = document.querySelector('.send-btn');
  
  if (!chatInput) return;
  
  if (status.available && status.status === 'ready') {
    // Enable chat
    chatInput.disabled = false;
    chatInput.placeholder = "Ask about this video...";
    if (sendButton) sendButton.disabled = false;
    
    // Add status message if this is a transition to ready
    if (!window.chatWasReady) {
      addChatMessage('🎉 Chat is now ready! You can ask questions about this video.', 'system');
      window.chatWasReady = true;
    }
  } else {
    // Disable chat with appropriate message
    chatInput.disabled = true;
    if (sendButton) sendButton.disabled = true;
    
    switch (status.status) {
      case 'processing':
        chatInput.placeholder = '⏳ Processing transcript for AI chat...';
        if (!window.processingMessageShown) {
          const retryMinutes = Math.round((status.retry_after || 120) / 60);
          addChatMessage(
            `🔄 ${status.message || 'Transcript is being processed for AI chat.'} Check back in ${retryMinutes} minutes or click the retry button.`,
            'system'
          );
          addRetryButton();
          window.processingMessageShown = true;
        }
        break;
        
      case 'not_found':
        chatInput.placeholder = '❌ Video not found. Extract transcript first.';
        addChatMessage('❌ Video transcript not found. Please click the "Get Transcript" button first.', 'system');
        break;
        
      case 'error':
      case 'rag_unavailable':
        chatInput.placeholder = '⚠️ Chat temporarily unavailable';
        addChatMessage(`⚠️ ${status.message || 'Chat is temporarily unavailable.'}`, 'system');
        break;
        
      default:
        chatInput.placeholder = '⏳ Chat not ready yet...';
        addChatMessage('⏳ Chat is not ready yet. Please wait for transcript processing.', 'system');
    }
  }
}

// Function to add retry button for chat status
function addRetryButton() {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return;
  
  // Check if retry button already exists
  if (document.getElementById('chat-retry-btn')) return;
  
  const retryDiv = document.createElement('div');
  retryDiv.className = 'chat-message system';
  retryDiv.innerHTML = `
    <div class="chat-content">
      <button id="chat-retry-btn" class="retry-chat-btn">🔄 Check Chat Status</button>
    </div>
  `;
  
  chatMessages.appendChild(retryDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  // Add click handler for retry button
  document.getElementById('chat-retry-btn').addEventListener('click', () => {
    if (window.currentVideoId) {
      checkChatStatus(window.currentVideoId);
    }
  });
}

// Chat status polling mechanism
let chatStatusPolling = null;

function startChatStatusPolling(videoId) {
  // Clear any existing polling
  if (chatStatusPolling) {
    clearInterval(chatStatusPolling);
    chatStatusPolling = null;
  }
  
  console.log('Starting chat status polling for video:', videoId);
  
  // Poll every 15 seconds (reasonable interval)
  chatStatusPolling = setInterval(async () => {
    console.log('Polling chat status for video:', videoId);
    
    try {
      const status = await checkChatStatus(videoId);
      
      if (status && status.available && status.status === 'ready') {
        console.log('Chat is now ready, stopping polling');
        clearInterval(chatStatusPolling);
        chatStatusPolling = null;
      }
    } catch (error) {
      console.error('Error during polling:', error);
      // Continue polling despite errors
    }
  }, 15000); // 15 seconds
  
  // Auto-stop polling after 10 minutes (40 polls) to prevent infinite polling
  setTimeout(() => {
    if (chatStatusPolling) {
      console.log('Stopping chat status polling after timeout');
      clearInterval(chatStatusPolling);
      chatStatusPolling = null;
    }
  }, 600000); // 10 minutes
}

function stopChatStatusPolling() {
  if (chatStatusPolling) {
    console.log('Manually stopping chat status polling');
    clearInterval(chatStatusPolling);
    chatStatusPolling = null;
  }
}

// Function to retry transcript fetching
function retryTranscript() {
  const videoUrl = window.location.href;
  const transcriptTab = document.getElementById('transcript-tab');
  
  // Reset chat state
  window.chatWasReady = false;
  window.processingMessageShown = false;
  stopChatStatusPolling();
  
  if (transcriptTab) {
    transcriptTab.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <h4>Getting Transcript...</h4>
        <p>Please wait while we extract the transcript from this video.</p>
      </div>
    `;
    fetchTranscript(videoUrl);
  }
}

// Function to toggle sidebar
function toggleSidebar() {
  let sidebar = document.getElementById('transcript-sidebar');
  
  if (!sidebar) {
    sidebar = createSidebar();
    document.body.appendChild(sidebar);
    
    // Animate in
    setTimeout(() => {
      sidebar.classList.add('open');
    }, 10);
    
    // Start fetching transcript
    const videoUrl = window.location.href;
    fetchTranscript(videoUrl);
  } else {
    if (sidebar.classList.contains('open')) {
      // Close sidebar
      sidebar.classList.remove('open');
      setTimeout(() => {
        if (sidebar.parentNode) {
          sidebar.parentNode.removeChild(sidebar);
        }
      }, 300);
    } else {
      // Open sidebar
      sidebar.classList.add('open');
    }
  }
}

// Function to create transcript button
function createTranscriptButton() {
  const button = document.createElement('button');
  button.id = 'transcript-extractor-btn';
  button.innerHTML = '📝 Get Transcript';
  button.className = 'transcript-btn';
  
  button.addEventListener('click', function() {
    const videoId = getVideoId();
    const videoUrl = window.location.href;
    
    if (videoId) {
      console.log('Video ID:', videoId);
      console.log('Video URL:', videoUrl);
      
      // Toggle sidebar
      toggleSidebar();
    } else {
      alert('Could not find video ID');
    }
  });
  
  return button;
}

// Function to inject the button into YouTube's UI
function injectButton() {
  // Wait for YouTube's player to load
  const checkForPlayer = setInterval(() => {
    const actionsContainer = document.querySelector('#actions');
    const existingButton = document.querySelector('#transcript-extractor-btn');
    
    if (actionsContainer && !existingButton) {
      const button = createTranscriptButton();
      
      // Create a container div
      const buttonContainer = document.createElement('div');
      buttonContainer.className = 'transcript-btn-container';
      buttonContainer.appendChild(button);
      
      // Insert after the like/dislike buttons
      const likeButton = actionsContainer.querySelector('#segmented-like-button');
      if (likeButton) {
        likeButton.parentNode.insertBefore(buttonContainer, likeButton.nextSibling);
      } else {
        actionsContainer.appendChild(buttonContainer);
      }
      
      clearInterval(checkForPlayer);
      console.log('Transcript button injected');
    }
  }, 1000);
  
  // Stop checking after 30 seconds
  setTimeout(() => {
    clearInterval(checkForPlayer);
  }, 30000);
}

// Handle YouTube's single-page app navigation
let currentUrl = window.location.href;

// Initial injection
if (window.location.pathname === '/watch') {
  injectButton();
}

// Listen for URL changes (YouTube SPA navigation)
const observer = new MutationObserver(() => {
  if (currentUrl !== window.location.href) {
    currentUrl = window.location.href;
    
    if (window.location.pathname === '/watch') {
      setTimeout(injectButton, 1000); // Delay to ensure page is loaded
    }
  }
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});

// Also listen for popstate events
window.addEventListener('popstate', () => {
  if (window.location.pathname === '/watch') {
    setTimeout(injectButton, 1000);
  }
});