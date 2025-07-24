#!/usr/bin/env python3

import requests
import json

def test_flask_server():
    """Test the Flask server with yt-dlp implementation"""
    url = "http://localhost:6000/transcript"
    data = {
        "url": "https://www.youtube.com/watch?v=jpSY4MlWX50"
    }
    
    print("Testing Flask server...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    
    try:
        response = requests.post(url, json=data, timeout=60)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Title: {result.get('title')}")
            print(f"Video ID: {result.get('video_id')}")
            print(f"Transcript entries: {len(result.get('transcript', []))}")
            
            # Show first few transcript entries
            transcript = result.get('transcript', [])
            if transcript:
                print("\nFirst few transcript entries:")
                for i, entry in enumerate(transcript[:3]):
                    print(f"  {entry['start']}: {entry['text']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_flask_server()