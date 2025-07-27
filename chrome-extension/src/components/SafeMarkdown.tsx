import { useMemo, useRef, useEffect } from 'react';
import { safeMarkdownToHtml, hasMarkdown } from '../utils/safeMarkdown';
import { jumpToTimestamp } from '../utils/safeTimestamps';
import { TimestampNavigation } from './TimestampNavigation';

interface SafeMarkdownProps {
  content: string;
  fallback?: string;
  timestamps?: string[];
}

/**
 * Safe markdown renderer with error boundary
 * Falls back to plain text if rendering fails
 */
export function SafeMarkdown({ content, fallback, timestamps }: SafeMarkdownProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const htmlContent = useMemo(() => {
    try {
      // If no markdown syntax detected, return plain text
      if (!hasMarkdown(content)) {
        return null; // Will render as plain <p> tag
      }

      return safeMarkdownToHtml(content);
    } catch (error) {
      console.warn('SafeMarkdown rendering failed:', error);
      return null; // Fall back to plain text
    }
  }, [content]);

  // Add event delegation for timestamp clicks
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      
      // Check if clicked element is a timestamp link
      if (target && target.classList.contains('timestamp-link')) {
        event.preventDefault();
        const secondsAttr = target.getAttribute('data-seconds');
        
        if (secondsAttr) {
          const seconds = parseInt(secondsAttr, 10);
          console.log('🕒 Timestamp clicked via event delegation:', seconds);
          jumpToTimestamp(seconds);
        }
      }
    };

    container.addEventListener('click', handleClick);
    
    return () => {
      container.removeEventListener('click', handleClick);
    };
  }, [htmlContent]);

  // If markdown parsing failed or no markdown detected, render plain text
  if (!htmlContent) {
    return (
      <div>
        <p>{content}</p>
        <TimestampNavigation 
          content={content} 
          structuredTimestamps={timestamps} 
        />
      </div>
    );
  }

  // Render markdown HTML safely
  try {
    return (
      <div>
        <div 
          ref={containerRef}
          className="markdown-content"
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
        <TimestampNavigation 
          content={content} 
          structuredTimestamps={timestamps} 
        />
      </div>
    );
  } catch (error) {
    console.warn('SafeMarkdown HTML rendering failed:', error);
    return <p>{fallback || content}</p>;
  }
}