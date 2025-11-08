#!/usr/bin/env python3

import subprocess
import tempfile
import os
import json
from pathlib import Path

video_url = 'https://www.youtube.com/watch?v=_GXNJ3V9lzg'

print(f'Testing yt-dlp with: {video_url}')

with tempfile.TemporaryDirectory() as temp_dir:
    os.chdir(temp_dir)
    
    # Test basic video info first
    info_cmd = ['yt-dlp', '--print-json', '--skip-download', video_url]
    print('\n=== Testing video info ===')
    try:
        info_result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=30)
        print(f'Info return code: {info_result.returncode}')
        if info_result.returncode != 0:
            print(f'Info STDERR: {info_result.stderr}')
        else:
            # Parse basic info
            try:
                video_info = json.loads(info_result.stdout)
                print(f'Video title: {video_info.get("title", "Unknown")}')
                print(f'Duration: {video_info.get("duration", "Unknown")} seconds')
                print(f'Available subtitles: {list(video_info.get("subtitles", {}).keys())}')
                print(f'Auto subtitles: {list(video_info.get("automatic_captions", {}).keys())}')
            except Exception as e:
                print(f'Could not parse video info JSON: {e}')
    except subprocess.TimeoutExpired:
        print('Video info command timed out')
    
    # Test subtitle extraction
    print('\n=== Testing subtitle extraction ===')
    cmd = [
        'yt-dlp',
        '--write-auto-subs',
        '--sub-langs', 'en',
        '--sub-format', 'vtt',
        '--skip-download',
        video_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f'Subtitle return code: {result.returncode}')
        print(f'STDOUT: {result.stdout}')
        if result.stderr:
            print(f'STDERR: {result.stderr}')
        
        files = list(Path('.').glob('*'))
        print(f'Files created: {files}')
    except subprocess.TimeoutExpired:
        print('Subtitle extraction timed out')