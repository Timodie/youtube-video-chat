/**
 * Safe markdown parser with error handling
 * No external dependencies, no DOM manipulation, no storage access
 */

/**
 * Safely parse markdown to HTML
 * Returns original text if parsing fails
 */
export function safeMarkdownToHtml(content: string): string {
  try {
    if (!content || typeof content !== 'string') {
      return content || '';
    }

    let html = content;

    // Headers (## Title -> <h4>Title</h4>)
    html = html.replace(/^### (.*$)/gm, '<h5>$1</h5>');
    html = html.replace(/^## (.*$)/gm, '<h4>$1</h4>');
    html = html.replace(/^# (.*$)/gm, '<h3>$1</h3>');

    // Bold (**text** -> <strong>text</strong>)
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic (*text* -> <em>text</em>)
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Inline code (`code` -> <code>code</code>)
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Code blocks (```code``` -> <pre><code>code</code></pre>)
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Bullet lists (- item -> <li>item</li>)
    html = html.replace(/^- (.*)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Blockquotes (> text -> <blockquote>text</blockquote>)
    html = html.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>');

    // Line breaks (double newline -> <br><br>, single newline -> <br>)
    html = html.replace(/\n\n/g, '<br><br>');
    html = html.replace(/\n/g, '<br>');

    // Clean up any multiple <br> tags
    html = html.replace(/(<br>){3,}/g, '<br><br>');

    return html;
  } catch (error) {
    console.warn('Markdown parsing failed, returning original text:', error);
    return content;
  }
}

/**
 * Check if content has markdown syntax
 */
export function hasMarkdown(content: string): boolean {
  if (!content || typeof content !== 'string') {
    return false;
  }

  const markdownPatterns = [
    /^#{1,3}\s+/m,     // Headers
    /\*\*.*?\*\*/,     // Bold
    /\*.*?\*/,         // Italic
    /`.*?`/,           // Code
    /```[\s\S]*?```/, // Code blocks
    /^[-*]\s+/m,       // Lists
    /^>\s+/m           // Blockquotes
  ];

  return markdownPatterns.some(pattern => pattern.test(content));
}