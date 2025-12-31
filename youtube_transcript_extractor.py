#!/usr/bin/env python3
"""
YouTube Transcript Extractor
Robust module for extracting transcripts from YouTube videos using yt-dlp.

Features:
- Prefers manual subtitles over automatic captions
- Supports English variants (en, en-US, en-GB, etc.)
- If no English track is exposed, but translated auto-captions exist,
  it attempts to derive English by stripping 'tlang' from a caption URL.
"""

import re
from typing import Dict, List, Optional

from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False


class TranscriptExtractor:
    """Extract and parse YouTube video transcripts using yt-dlp Python library"""

    def __init__(self):
        """
        Initialize the transcript extractor

        Raises:
            RuntimeError: If yt-dlp is not installed
        """
        if not YTDLP_AVAILABLE:
            raise RuntimeError(
                "yt-dlp Python module not found. Please install it:\n"
                "  pip install yt-dlp\n"
                "or:\n"
                "  pip3 install yt-dlp"
            )

    @staticmethod
    def extract_video_id(url: str) -> str:
        """
        Extract video ID from YouTube URL

        Args:
            url: YouTube video URL or video ID

        Returns:
            Video ID string
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # Assume it's already a video ID
        return url

    @staticmethod
    def _strip_tlang_from_url(url: str) -> str:
        """
        Remove the 'tlang' parameter from a YouTube timedtext URL to try to get
        the original (base) language captions.

        Args:
            url: URL to modify

        Returns:
            URL without 'tlang' parameter
        """
        parsed = urlparse(url)
        qs = parse_qsl(parsed.query, keep_blank_values=True)
        qs = [(k, v) for (k, v) in qs if k != "tlang"]
        new_query = urlencode(qs)
        return urlunparse(parsed._replace(query=new_query))

    def get_transcript(self, video_url: str) -> Dict:
        """
        Extract transcript from YouTube video using yt-dlp Python library

        Args:
            video_url: YouTube video URL or ID

        Returns:
            Dictionary containing:
                - video_id: str
                - title: str
                - transcript: List[Dict] with start, end, text, start_seconds, end_seconds
                - url: str
                - language: str (language code used)
                - source: str ('subtitles', 'automatic_captions', or 'automatic_captions_hacked')
                - match_type: str ('exact', 'variant', 'fallback-any', 'hacked-from-translation')

        Raises:
            Exception: If transcript extraction fails
        """
        video_id = self.extract_video_id(video_url)
        video_url_full = f'https://www.youtube.com/watch?v={video_id}'

        # Configure yt-dlp options
        ydl_opts = {
            'writeautomaticsub': True,      # Get auto-generated subtitles
            'writeinfojson': False,
            'subtitleslangs': ['en'],       # Request English subtitles (if any)
            'subtitlesformat': 'vtt',       # Prefer VTT format
            'skip_download': True,          # Don't download video
            'quiet': True,                  # Suppress output
            'no_warnings': True,            # Suppress warnings
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info and subtitles
                info = ydl.extract_info(video_url_full, download=False)

                if not info:
                    raise Exception(f"Could not extract video info for {video_id}")

                # Get video title
                title = info.get('title', 'Unknown Title')

                subtitles = info.get("subtitles") or {}
                automatic_captions = info.get("automatic_captions") or {}

                # -------- Language selection helpers --------

                def pick_lang(caption_dict, preferred_prefixes=("en",)):
                    """
                    Pick a language track from a caption dict, preferring exact 'en'
                    then any 'en-*' variant (e.g. 'en-US', 'en-GB').

                    Returns:
                        (lang_code, tracks, match_type)
                    """
                    if not caption_dict:
                        return None, None, None

                    # Exact matches first
                    for pref in preferred_prefixes:
                        if pref in caption_dict:
                            return pref, caption_dict[pref], "exact"

                    # Variants like en-US, en-GB...
                    for pref in preferred_prefixes:
                        for lang_code in caption_dict.keys():
                            if lang_code.startswith(pref):
                                return lang_code, caption_dict[lang_code], "variant"

                    return None, None, None

                def pick_lang_with_fallback(subtitles_dict, auto_dict,
                                            preferred_prefixes=("en",),
                                            fallback_any=False):
                    """
                    Try, in order:
                      1. manual subtitles matching any preferred prefix
                      2. automatic captions matching any preferred prefix
                      3. if fallback_any: first available manual subtitle
                      4. if fallback_any: first available automatic caption

                    Returns:
                        (lang_code, tracks, source, match_type)
                    """
                    # Manual subtitles
                    lang_code, tracks, match_type = pick_lang(subtitles_dict, preferred_prefixes)
                    source = "subtitles"
                    if tracks:
                        return lang_code, tracks, source, match_type

                    # Automatic captions
                    lang_code, tracks, match_type = pick_lang(auto_dict, preferred_prefixes)
                    source = "automatic_captions"
                    if tracks:
                        return lang_code, tracks, source, match_type

                    # Fallback to any language if allowed
                    if fallback_any:
                        if subtitles_dict:
                            lang_code = next(iter(subtitles_dict.keys()))
                            tracks = subtitles_dict[lang_code]
                            source = "subtitles"
                            match_type = "fallback-any"
                        elif auto_dict:
                            lang_code = next(iter(auto_dict.keys()))
                            tracks = auto_dict[lang_code]
                            source = "automatic_captions"
                            match_type = "fallback-any"
                        else:
                            lang_code = tracks = source = match_type = None
                        return lang_code, tracks, source, match_type

                    return None, None, None, None

                # -------- Try to get English or an English variant normally --------

                lang_code, tracks, source, match_type = pick_lang_with_fallback(
                    subtitles,
                    automatic_captions,
                    preferred_prefixes=("en",),
                    fallback_any=False,  # we will do a smarter fallback below
                )

                vtt_url = None
                hacked = False

                if tracks:
                    # We found an English/variant track normally
                    vtt_subtitle = next((c for c in tracks if c.get("ext") == "vtt"), None)
                    if not vtt_subtitle:
                        raise Exception(
                            f"VTT format not available for language '{lang_code}' "
                            f"from {source} for video {video_id}"
                        )
                    vtt_url = vtt_subtitle["url"]

                # -------- HACK: derive English from translated auto-captions --------
                else:
                    # No English/variant track found, but maybe there are translated
                    # auto-captions (ar, fr, etc.) whose URLs include
                    # lang=en&tlang=<something>. We can strip 'tlang' to try to get
                    # the underlying English ASR.
                    if automatic_captions:
                        # Just pick the first language's tracks
                        first_lang_code, tracks_list = next(iter(automatic_captions.items()))

                        # Prefer VTT here as well
                        vtt_subtitle = next((c for c in tracks_list if c.get("ext") == "vtt"), None)
                        if not vtt_subtitle:
                            raise Exception(
                                "No VTT format found in automatic_captions to hack English from. "
                                f"Languages present: {list(automatic_captions.keys())}"
                            )

                        hacked_url = self._strip_tlang_from_url(vtt_subtitle["url"])
                        vtt_url = hacked_url
                        lang_code = "en"
                        source = "automatic_captions_hacked"
                        match_type = "hacked-from-translation"
                        hacked = True
                    else:
                        # Truly nothing we can do
                        raise Exception(
                            f"No English subtitles or auto-generated captions found for video {video_id}. "
                            f"Subtitle languages: {list(subtitles.keys()) or 'none'}, "
                            f"auto-caption languages: {list(automatic_captions.keys()) or 'none'}"
                        )

                # -------- Download and parse the VTT content --------

                import urllib.request
                if not vtt_url:
                    raise Exception("Could not determine a VTT URL for subtitles.")

                with urllib.request.urlopen(vtt_url) as response:
                    vtt_content = response.read().decode('utf-8')

                transcript_data = self._parse_vtt(vtt_content)

                return {
                    'video_id': video_id,
                    'title': title,
                    'transcript': transcript_data,
                    'url': video_url_full,
                    'language': lang_code,
                    'source': source,
                    'match_type': match_type,
                    'hacked_from_translation': hacked,
                }

        except yt_dlp.utils.DownloadError as e:
            raise Exception(f"Failed to download video info: {str(e)}")
        except Exception as e:
            raise Exception(f"Transcript extraction failed for {video_id}: {str(e)}")

    @staticmethod
    def _parse_vtt(vtt_content: str) -> List[Dict]:
        """
        Parse VTT content into structured transcript data

        Args:
            vtt_content: Raw VTT file content

        Returns:
            List of dictionaries with transcript entries
        """
        lines = vtt_content.split('\n')
        transcript_data = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for timestamp lines (format: "00:00:00.000 --> 00:00:03.000")
            if '-->' in line:
                parts = line.split(' --> ')
                if len(parts) == 2:
                    start_time_str = parts[0].strip()
                    end_time_str = parts[1].strip()

                    # Convert to seconds
                    start_seconds = TranscriptExtractor._time_str_to_seconds(start_time_str)
                    end_seconds = TranscriptExtractor._time_str_to_seconds(end_time_str)

                    # Get the text (next non-empty lines)
                    text_lines = []
                    i += 1
                    while i < len(lines) and lines[i].strip():
                        text_lines.append(lines[i].strip())
                        i += 1

                    if text_lines:
                        text = ' '.join(text_lines)
                        # Remove VTT formatting tags
                        text = re.sub(r'<[^>]+>', '', text)

                        transcript_data.append({
                            'start': start_time_str,
                            'end': end_time_str,
                            'text': text,
                            'start_seconds': start_seconds,
                            'end_seconds': end_seconds
                        })

            i += 1

        return transcript_data

    @staticmethod
    def _time_str_to_seconds(time_str: str) -> float:
        """
        Convert VTT time string to seconds

        Args:
            time_str: Time string in format HH:MM:SS.mmm (may include VTT alignment attributes)

        Returns:
            Time in seconds as float
        """
        try:
            # Clean VTT alignment attributes (e.g., "00:00:02.240 align:start position:0%")
            clean_time = time_str.split(' ')[0]  # Take only the time part before any spaces

            parts = clean_time.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            return total_seconds
        except Exception as e:
            print(f"⚠️ Error parsing time string '{time_str}': {e}")
            return 0.0


# Standalone function for backward compatibility
def get_youtube_transcript(video_url: str) -> Dict:
    """
    Convenience function to extract transcript

    Args:
        video_url: YouTube video URL or ID

    Returns:
        Dictionary with video_id, title, and transcript data
    """
    extractor = TranscriptExtractor()
    return extractor.get_transcript(video_url)


# CLI interface
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python youtube_transcript_extractor.py <youtube_url> [--json]")
        print("\nExample:")
        print("  python youtube_transcript_extractor.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
        sys.exit(1)

    video_url = sys.argv[1]

    try:
        print(f"🎥 Extracting transcript for: {video_url}")

        extractor = TranscriptExtractor()
        result = extractor.get_transcript(video_url)

        print(f"\n✅ Success!")
        print(f"📝 Title: {result['title']}")
        print(f"🆔 Video ID: {result['video_id']}")
        print(f"🌐 Language used: {result.get('language')}")
        print(f"📦 Source: {result.get('source')} (match_type={result.get('match_type')})")
        print(f"📊 Transcript entries: {len(result['transcript'])}")

        # Show first few entries
        if result['transcript']:
            print(f"\n📄 First 3 transcript entries:")
            for i, entry in enumerate(result['transcript'][:3]):
                print(f"\n  {i+1}. [{entry['start']} --> {entry['end']}]")
                print(f"     {entry['text']}")

        # Optionally save to JSON
        if len(sys.argv) > 2 and sys.argv[2] == '--json':
            output_file = f"{result['video_id']}_transcript.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
