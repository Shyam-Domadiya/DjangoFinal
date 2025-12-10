// Auto-refresh functionality for dynamic content updates
// This runs silently in the background with NO UI buttons or controls
class AutoRefresh {
    constructor() {
        this.intervals = new Map();
        this.isEnabled = true;
        this.defaultInterval = 10000; // 10 seconds
        this.init();
    }

    init() {
        // Remove any existing auto-refresh buttons that might be in the DOM
        const existingButton = document.getElementById('refreshToggle');
        if (existingButton) {
            existingButton.remove();
        }
        
        // Start auto-refresh for appropriate pages (enabled by default)
        if (this.shouldAutoRefresh()) {
            this.startAutoRefresh();
        }
        
        // Listen for visibility changes to pause/resume
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAll();
            } else {
                this.resumeAll();
            }
        });
    }

    shouldAutoRefresh() {
        const path = window.location.pathname;
        return path === '/' || path === '/tweets/' || path.includes('/tweet/');
    }



    startAutoRefresh() {
        const path = window.location.pathname;
        
        if (path === '/' || path === '/tweets/') {
            this.startTweetListRefresh();
        } else if (path.includes('/tweet/')) {
            this.startTweetDetailRefresh();
        }
    }

    startTweetListRefresh() {
        const refreshId = 'tweetList';
        
        this.intervals.set(refreshId, setInterval(() => {
            this.refreshTweetList();
        }, this.defaultInterval));
    }

    startTweetDetailRefresh() {
        const refreshId = 'tweetDetail';
        
        this.intervals.set(refreshId, setInterval(() => {
            this.refreshTweetDetail();
        }, this.defaultInterval));
    }

    async refreshTweetList() {
        try {
            const response = await fetch(window.location.href, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Update tweets grid
            const currentGrid = document.querySelector('.tweets-grid');
            const newGrid = doc.querySelector('.tweets-grid');
            
            if (currentGrid && newGrid) {
                // Check if content has changed
                if (currentGrid.innerHTML !== newGrid.innerHTML) {
                    currentGrid.innerHTML = newGrid.innerHTML;
                    
                    // Re-attach event listeners for new content
                    this.reattachEventListeners();
                }
            }
            
        } catch (error) {
            console.error('Auto-refresh error:', error);
        }
    }

    async refreshTweetDetail() {
        try {
            const response = await fetch(window.location.href, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Update comments section
            const currentComments = document.querySelector('.comments-list');
            const newComments = doc.querySelector('.comments-list');
            
            if (currentComments && newComments) {
                if (currentComments.innerHTML !== newComments.innerHTML) {
                    currentComments.innerHTML = newComments.innerHTML;
                }
            }
            
            // Update like count
            const currentLikeCount = document.querySelector('.like-count');
            const newLikeCount = doc.querySelector('.like-count');
            
            if (currentLikeCount && newLikeCount) {
                if (currentLikeCount.textContent !== newLikeCount.textContent) {
                    currentLikeCount.textContent = newLikeCount.textContent;
                }
            }
            
        } catch (error) {
            console.error('Auto-refresh error:', error);
        }
    }

    reattachEventListeners() {
        // Re-attach like button listeners
        document.querySelectorAll('.like-btn').forEach(btn => {
            const tweetId = btn.getAttribute('data-tweet-id') || 
                           btn.closest('[data-tweet-id]')?.getAttribute('data-tweet-id');
            if (tweetId) {
                btn.onclick = () => toggleLike(tweetId, btn);
            }
        });

        // Re-attach delete button listeners
        document.querySelectorAll('[onclick*="deleteTweet"]').forEach(btn => {
            const tweetId = btn.getAttribute('data-tweet-id') || 
                           btn.closest('[data-tweet-id]')?.getAttribute('data-tweet-id');
            if (tweetId) {
                btn.onclick = () => deleteTweet(tweetId);
            }
        });
    }



    pauseAll() {
        this.intervals.forEach((interval, id) => {
            clearInterval(interval);
        });
    }

    resumeAll() {
        if (this.isEnabled) {
            this.intervals.clear();
            this.startAutoRefresh();
        }
    }

    stopAll() {
        this.pauseAll();
        this.intervals.clear();
        this.isEnabled = false;
    }




}



// Initialize auto-refresh when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.autoRefresh = new AutoRefresh();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.autoRefresh) {
        window.autoRefresh.stopAll();
    }
});