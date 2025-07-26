import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import Sidebar from './components/Sidebar';
import TranscriptButton from './components/TranscriptButton';
import { useVideoId } from './hooks/useVideoId';
import '../content.css';

console.log('YouTube Transcript Extractor (React) loaded');

function App() {
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [buttonInjected, setButtonInjected] = useState(false);
  const videoId = useVideoId();

  // Inject transcript button when video changes
  useEffect(() => {
    if (videoId && window.location.pathname === '/watch') {
      injectTranscriptButton();
    } else {
      setButtonInjected(false);
      setSidebarVisible(false);
    }
  }, [videoId]);

  const injectTranscriptButton = () => {
    if (buttonInjected) return;

    const checkForPlayer = setInterval(() => {
      const actionsContainer = document.querySelector('#actions');
      const existingButton = document.querySelector('#transcript-extractor-btn');
      
      if (actionsContainer && !existingButton) {
        // Create container for React button
        const buttonContainer = document.createElement('div');
        buttonContainer.id = 'transcript-button-root';
        
        // Insert after the like/dislike buttons
        const likeButton = actionsContainer.querySelector('#segmented-like-button');
        if (likeButton) {
          likeButton.parentNode.insertBefore(buttonContainer, likeButton.nextSibling);
        } else {
          actionsContainer.appendChild(buttonContainer);
        }
        
        // Render React button
        const buttonRoot = createRoot(buttonContainer);
        buttonRoot.render(
          <TranscriptButton 
            videoId={videoId} 
            onClick={() => setSidebarVisible(true)} 
          />
        );
        
        setButtonInjected(true);
        clearInterval(checkForPlayer);
        console.log('Transcript button injected (React)');
      }
    }, 1000);
    
    // Stop checking after 30 seconds
    setTimeout(() => {
      clearInterval(checkForPlayer);
    }, 30000);
  };

  return (
    <>
      {sidebarVisible && (
        <Sidebar 
          videoId={videoId} 
          onClose={() => setSidebarVisible(false)} 
        />
      )}
    </>
  );
}

// Initialize the React app
function initializeApp() {
  // Create root container for the app
  const appContainer = document.createElement('div');
  appContainer.id = 'transcript-app-root';
  document.body.appendChild(appContainer);
  
  // Render the app
  const root = createRoot(appContainer);
  root.render(<App />);
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}