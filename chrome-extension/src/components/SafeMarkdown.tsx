import { useMemo } from 'react';
import { safeMarkdownToHtml, hasMarkdown } from '../utils/safeMarkdown';

interface SafeMarkdownProps {
  content: string;
  fallback?: string;
}

/**
 * Safe markdown renderer with error boundary
 * Falls back to plain text if rendering fails
 */
export function SafeMarkdown({ content, fallback }: SafeMarkdownProps) {
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

  // If markdown parsing failed or no markdown detected, render plain text
  if (!htmlContent) {
    return <p>{content}</p>;
  }

  // Render markdown HTML safely
  try {
    return (
      <div 
        className="markdown-content"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
    );
  } catch (error) {
    console.warn('SafeMarkdown HTML rendering failed:', error);
    return <p>{fallback || content}</p>;
  }
}