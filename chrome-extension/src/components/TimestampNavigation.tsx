import { useMemo } from 'react';
import { parseTimestamps, jumpToTimestamp, formatTimestamp } from '../utils/safeTimestamps';

interface TimestampNavigationProps {
  content: string;
  structuredTimestamps?: string[];
}

interface ParsedTimestamp {
  original: string;
  totalSeconds: number;
  source: 'text' | 'structured';
}

/**
 * Timestamp navigation bar that shows both inline and structured timestamps
 * Deduplicates and sorts them chronologically
 */
export function TimestampNavigation({ content, structuredTimestamps }: TimestampNavigationProps) {
  const allTimestamps = useMemo(() => {
    const timestamps: ParsedTimestamp[] = [];

    // Parse timestamps from text content
    const textTimestamps = parseTimestamps(content);
    textTimestamps.forEach(ts => {
      timestamps.push({
        original: ts.original,
        totalSeconds: ts.totalSeconds,
        source: 'text'
      });
    });

    // Add structured timestamps from API
    if (structuredTimestamps && structuredTimestamps.length > 0) {
      structuredTimestamps.forEach(tsStr => {
        const parsed = parseTimestamps(tsStr);
        parsed.forEach(ts => {
          // Check if this timestamp already exists from text parsing
          const exists = timestamps.some(existing => 
            Math.abs(existing.totalSeconds - ts.totalSeconds) < 5 // Within 5 seconds = same timestamp
          );
          
          if (!exists) {
            timestamps.push({
              original: ts.original,
              totalSeconds: ts.totalSeconds,
              source: 'structured'
            });
          }
        });
      });
    }

    // Sort by time and remove duplicates
    return timestamps
      .sort((a, b) => a.totalSeconds - b.totalSeconds)
      .filter((ts, index, arr) => 
        index === 0 || Math.abs(ts.totalSeconds - arr[index - 1].totalSeconds) >= 5
      );
  }, [content, structuredTimestamps]);

  const handleTimestampClick = (seconds: number) => {
    console.log('🕒 Navigation timestamp clicked:', seconds);
    jumpToTimestamp(seconds);
  };

  // Don't render if no timestamps found
  if (allTimestamps.length === 0) {
    return null;
  }

  return (
    <div className="timestamp-navigation">
      <div className="timestamp-navigation-label">Quick Navigation:</div>
      <div className="timestamp-navigation-bar">
        {allTimestamps.map((ts, index) => (
          <button
            key={`${ts.totalSeconds}-${index}`}
            className={`timestamp-nav-button ${ts.source}`}
            onClick={() => handleTimestampClick(ts.totalSeconds)}
            title={`Jump to ${formatTimestamp(ts.totalSeconds)} (from ${ts.source})`}
          >
            {formatTimestamp(ts.totalSeconds)}
          </button>
        ))}
      </div>
    </div>
  );
}