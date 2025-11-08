#!/usr/bin/env python3

import subprocess
import tempfile
import os
import json
from pathlib import Path

def test_subtitle_extraction(video_url, test_name):
    print(f'\n=== {test_name} ===')
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        try:
            result = subprocess.run(
                ['yt-dlp', '--write-auto-subs', '--sub-langs', 'en,en-US', 
                 '--sub-format', 'vtt', '--skip-download', video_url],
                capture_output=True, text=True, timeout=60
            )
            
            print(f'Return code: {result.returncode}')
            print(f'STDOUT: {result.stdout}')
            if result.stderr:
                print(f'STDERR: {result.stderr}')
            
            files = list(Path('.').glob('*'))
            print(f'Files created: {files}')
            
            if files:
                # Try to read first few lines of any VTT file
                for file in files:
                    if file.suffix == '.vtt':
                        print(f'\nFirst few lines of {file}:')
                        with open(file, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f):
                                if i < 10:
                                    print(f'  {line.strip()}')
                                else:
                                    break
                        break
                        
        except subprocess.TimeoutExpired:
            print('Command timed out')
        except Exception as e:
            print(f'Error: {e}')

# Test different approaches
video_url = 'https://www.youtube.com/watch?v=_GXNJ3V9lzg'

print('Testing Jon Stewart video with different subtitle extraction methods')

# Test 1: Current method
test_subtitle_extraction(video_url, 'Test 1: Current method (en only)')

# Test 2: Try with both en and en-US
print('\n=== Test 2: Both en and en-US languages ===')
with tempfile.TemporaryDirectory() as temp_dir:
    os.chdir(temp_dir)
    try:
        result = subprocess.run([
            'yt-dlp', '--write-auto-subs', '--sub-langs', 'en,en-US', 
            '--sub-format', 'vtt', '--skip-download', video_url
        ], capture_output=True, text=True, timeout=60)
        
        print(f'Return code: {result.returncode}')
        print(f'STDOUT: {result.stdout}')
        if result.stderr:
            print(f'STDERR: {result.stderr}')
        
        files = list(Path('.').glob('*'))
        print(f'Files created: {files}')
    except Exception as e:
        print(f'Error: {e}')

# Test 3: Try without auto-subs, just regular subs
print('\n=== Test 3: Regular subtitles (no auto) ===')
with tempfile.TemporaryDirectory() as temp_dir:
    os.chdir(temp_dir)
    try:
        result = subprocess.run([
            'yt-dlp', '--write-subs', '--sub-langs', 'en,en-US', 
            '--sub-format', 'vtt', '--skip-download', video_url
        ], capture_output=True, text=True, timeout=60)
        
        print(f'Return code: {result.returncode}')
        print(f'STDOUT: {result.stdout}')
        if result.stderr:
            print(f'STDERR: {result.stderr}')
        
        files = list(Path('.').glob('*'))
        print(f'Files created: {files}')
    except Exception as e:
        print(f'Error: {e}')

# Test 4: Try with cookies/headers to avoid 403
print('\n=== Test 4: With user agent ===')
with tempfile.TemporaryDirectory() as temp_dir:
    os.chdir(temp_dir)
    try:
        result = subprocess.run([
            'yt-dlp', '--write-auto-subs', '--sub-langs', 'en,en-US', 
            '--sub-format', 'vtt', '--skip-download',
            '--user-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            video_url
        ], capture_output=True, text=True, timeout=60)
        
        print(f'Return code: {result.returncode}')
        print(f'STDOUT: {result.stdout}')
        if result.stderr:
            print(f'STDERR: {result.stderr}')
        
        files = list(Path('.').glob('*'))
        print(f'Files created: {files}')
    except Exception as e:
        print(f'Error: {e}')