import { useState, useEffect } from 'react';
import { getCurrentVideoId } from '../services/api';

/**
 * Hook to track current YouTube video ID
 * Handles URL changes in YouTube's SPA navigation
 */
export function useVideoId(): string | null {
  const [videoId, setVideoId] = useState<string | null>(() => getCurrentVideoId());

  useEffect(() => {
    let currentUrl = window.location.href;

    // Listen for URL changes (YouTube SPA navigation)
    const observer = new MutationObserver(() => {
      if (currentUrl !== window.location.href) {
        currentUrl = window.location.href;
        const newVideoId = getCurrentVideoId();
        setVideoId(newVideoId);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Also listen for popstate events
    const handlePopState = (): void => {
      const newVideoId = getCurrentVideoId();
      setVideoId(newVideoId);
    };

    window.addEventListener('popstate', handlePopState);

    return () => {
      observer.disconnect();
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  return videoId;
}