// Popup script for YouTube Transcript Extractor

document.addEventListener('DOMContentLoaded', function() {
  const openYoutubeBtn = document.getElementById('openYoutube');
  const viewOptionsBtn = document.getElementById('viewOptions');
  
  // Open YouTube in new tab
  openYoutubeBtn.addEventListener('click', function() {
    chrome.tabs.create({ url: 'https://www.youtube.com' });
    window.close();
  });
  
  // View options (placeholder)
  viewOptionsBtn.addEventListener('click', function() {
    alert('Options coming soon! For now, just navigate to any YouTube video and click the "📝 Get Transcript" button.');
  });
  
  // Check if current tab is YouTube
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const currentTab = tabs[0];
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    const statusValue = document.querySelector('.info-value');
    
    if (currentTab.url && currentTab.url.includes('youtube.com/watch')) {
      statusDot.style.background = '#28a745';
      statusText.textContent = 'YouTube Video Detected';
      statusValue.textContent = 'Ready';
    } else if (currentTab.url && currentTab.url.includes('youtube.com')) {
      statusDot.style.background = '#ffc107';
      statusText.textContent = 'On YouTube';
      statusValue.textContent = 'Navigate to video';
    } else {
      statusDot.style.background = '#dc3545';
      statusText.textContent = 'Not on YouTube';
      statusValue.textContent = 'Navigate to YouTube';
    }
  });
});