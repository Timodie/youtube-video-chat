/**
 * Safe timestamp handling without aggressive DOM manipulation
 */

interface TimestampMatch {
  original: string;
  minutes: number;
  seconds: number;
  totalSeconds: number;
}

/**
 * Parse timestamp formats from text
 * Supports: [MM:SS], (MM:SS), MM:SS, [HH:MM:SS], etc.
 */
export function parseTimestamps(text: string): TimestampMatch[] {
  try {
    if (!text || typeof text !== 'string') {
      return [];
    }

    // Updated regex to handle both MM:SS and HH:MM:SS formats
    const timestampRegex = /(?:\[|\()?(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:\]|\))?/g;
    const matches: TimestampMatch[] = [];
    let match;

    while ((match = timestampRegex.exec(text)) !== null) {
      const hours = match[1] ? parseInt(match[1], 10) : 0;
      const minutes = parseInt(match[2], 10);
      const seconds = parseInt(match[3], 10);
      const totalSeconds = hours * 3600 + minutes * 60 + seconds;

      console.log('🕒 Parsing timestamp:', match[0], '→', { hours, minutes, seconds, totalSeconds });

      // Validate reasonable timestamp ranges
      if (totalSeconds >= 0 && totalSeconds <= 86400) { // Max 24 hours
        matches.push({
          original: match[0],
          minutes: hours * 60 + minutes, // Store total minutes for backward compatibility
          seconds,
          totalSeconds,
        });
      }
    }

    return matches;
  } catch (error) {
    console.warn('Timestamp parsing failed:', error);
    return [];
  }
}

/**
 * Convert seconds to MM:SS format
 */
export function formatTimestamp(seconds: number): string {
  try {
    if (typeof seconds !== 'number' || seconds < 0) {
      return '0:00';
    }

    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  } catch (error) {
    console.warn('Timestamp formatting failed:', error);
    return '0:00';
  }
}

/**
 * Navigate to timestamp in YouTube video (safe version)
 */
export function jumpToTimestamp(seconds: number): boolean {
  try {
    if (typeof seconds !== 'number' || seconds < 0) {
      console.warn('Invalid timestamp:', seconds);
      return false;
    }

    const video = document.querySelector('video') as HTMLVideoElement;
    if (video && typeof video.currentTime !== 'undefined') {
      video.currentTime = seconds;
      console.log(`Jumped to ${formatTimestamp(seconds)}`);
      return true;
    } else {
      console.warn('No video element found or currentTime not available');
      return false;
    }
  } catch (error) {
    console.warn('Jump to timestamp failed:', error);
    return false;
  }
}

/**
 * Make timestamps clickable in markdown content (React-friendly version)
 */
export function makeTimestampsClickable(html: string): string {
  try {
    if (!html || typeof html !== 'string') {
      return html || '';
    }

    // Updated regex to handle both MM:SS and HH:MM:SS formats
    const timestampRegex = /(?:\[|\()?(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:\]|\))?/g;
    
    const result = html.replace(timestampRegex, (match, hours, minutes, seconds) => {
      const h = hours ? parseInt(hours, 10) : 0;
      const m = parseInt(minutes, 10);
      const s = parseInt(seconds, 10);
      const totalSeconds = h * 3600 + m * 60 + s;
      
      const displayTime = h > 0 ? `${h}:${minutes}:${seconds}` : `${minutes}:${seconds}`;
      
      console.log('🕒 Found timestamp:', match, '→', { h, m, s, totalSeconds }, 'seconds');
      
      // Use data attribute for event delegation (more reliable than onclick)
      return `<span class="timestamp-link" data-seconds="${totalSeconds}" title="Jump to ${displayTime}">${match}</span>`;
    });
    
    if (result !== html) {
      console.log('✅ Timestamps made clickable in content');
    }
    
    return result;
  } catch (error) {
    console.warn('❌ Making timestamps clickable failed:', error);
    return html;
  }
}

/**
 * Initialize global timestamp handler (called once)
 * Note: With event delegation, we don't need a global handler anymore
 */
export function initializeTimestampHandler(): void {
  console.log('✅ Timestamp handler initialized (using event delegation)');
}