import { useState, useEffect, useRef } from 'react';
import { createRoot, Root } from 'react-dom/client';
import Sidebar from './components/Sidebar';
import TranscriptButton from './components/TranscriptButton';
import { useVideoId } from './hooks/useVideoId';
import '../content.css';

console.log('YouTube Transcript Extractor (React) loaded');

function App() {
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [buttonInjected, setButtonInjected] = useState(false);
  const videoId = useVideoId();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const buttonRootRef = useRef<Root | null>(null);

  // Inject transcript button when video changes
  useEffect(() => {
    if (videoId && window.location.pathname === '/watch') {
      injectTranscriptButton();
    } else {
      cleanupButton();
      setButtonInjected(false);
      setSidebarVisible(false);
    }
  }, [videoId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupButton();
    };
  }, []);

  const cleanupButton = () => {
    // Clear intervals and timeouts
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    
    // Unmount React button root
    if (buttonRootRef.current) {
      buttonRootRef.current.unmount();
      buttonRootRef.current = null;
    }
    
    // Remove button container
    const buttonContainer = document.querySelector('#transcript-button-root');
    if (buttonContainer) {
      buttonContainer.remove();
    }
  };

  const injectTranscriptButton = () => {
    if (buttonInjected) return;

    intervalRef.current = setInterval(() => {
      const actionsContainer = document.querySelector('#actions');
      const existingButton = document.querySelector('#transcript-extractor-btn');
      
      if (actionsContainer && !existingButton) {
        // Create container for React button
        const buttonContainer = document.createElement('div');
        buttonContainer.id = 'transcript-button-root';
        
        // Insert after the like/dislike buttons
        const likeButton = actionsContainer.querySelector('#segmented-like-button');
        if (likeButton && likeButton.parentNode) {
          likeButton.parentNode.insertBefore(buttonContainer, likeButton.nextSibling);
        } else {
          actionsContainer.appendChild(buttonContainer);
        }
        
        // Render React button
        buttonRootRef.current = createRoot(buttonContainer);
        buttonRootRef.current.render(
          <TranscriptButton 
            videoId={videoId} 
            onClick={() => setSidebarVisible(true)} 
          />
        );
        
        setButtonInjected(true);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        console.log('Transcript button injected (React)');
      }
    }, 1000);
    
    // Stop checking after 30 seconds
    timeoutRef.current = setTimeout(() => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
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

// Global app root reference for cleanup
let appRoot: Root | null = null;

// Initialize the React app
function initializeApp() {
  // Create root container for the app
  const appContainer = document.createElement('div');
  appContainer.id = 'transcript-app-root';
  document.body.appendChild(appContainer);
  
  // Render the app
  appRoot = createRoot(appContainer);
  appRoot.render(<App />);
}

// Cleanup function for extension unload
function cleanupApp() {
  if (appRoot) {
    appRoot.unmount();
    appRoot = null;
  }
  
  const appContainer = document.querySelector('#transcript-app-root');
  if (appContainer) {
    appContainer.remove();
  }
}

// Handle extension unload/reload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', cleanupApp);
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}