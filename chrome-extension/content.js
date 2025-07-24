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
function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  
  if (!message) return;
  
  // Clear input
  input.value = '';
  
  // Add user message
  addChatMessage(message, 'user');
  
  // Add loading bubble
  addLoadingMessage();
  
  // Simulate AI response after delay
  setTimeout(() => {
    removeLoadingMessage();
    addChatMessage('AI chat functionality is coming soon! 🚀\n\nI\'ll be able to discuss this video\'s content, answer questions, and provide insights based on the transcript.', 'ai');
  }, 1500);
}

// Function to add chat message
function addChatMessage(message, sender) {
  const chatMessages = document.getElementById('chat-messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `${sender}-message`;
  
  if (sender === 'user') {
    messageDiv.innerHTML = `
      <div class="message-avatar">👤</div>
      <div class="message-content">
        <p>${message}</p>
      </div>
    `;
  } else {
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
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'ai-message loading-message';
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

// Function to fetch transcript from Flask server
async function fetchTranscript(videoUrl) {
  try {
    const response = await fetch('http://localhost:8080/transcript', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: videoUrl })
    });
    
    const data = await response.json();
    
    if (data.success) {
      displayTranscript(data);
    } else {
      displayError(data.error || 'Failed to get transcript');
    }
  } catch (error) {
    console.error('Error fetching transcript:', error);
    displayError('Could not connect to transcript server. Make sure the Flask server is running on localhost:8080');
  }
}

// Function to display transcript in sidebar
function displayTranscript(data) {
  const transcriptTab = document.getElementById('transcript-tab');
  if (!transcriptTab) return;
  
  transcriptTab.innerHTML = `
    <div class="transcript-header">
      <h4>${data.title}</h4>
      <p class="video-info">Language: ${data.language} (${data.language_code})</p>
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

// Function to retry transcript fetching
function retryTranscript() {
  const videoUrl = window.location.href;
  const transcriptTab = document.getElementById('transcript-tab');
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