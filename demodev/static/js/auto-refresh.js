// Auto-refresh functionality for dynamic content updates
class AutoRefresh {
    constructor() {
        this.intervals = new Map();
        this.isEnabled = true;
        this.defaultInterval = 10000; // 10 seconds
        this.init();
    }

    init() {
        // Add refresh controls to pages
        this.addRefreshControls();
        
        // Start auto-refresh for appropriate pages
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

    addRefreshControls() {
        // Add refresh toggle button to navbar
        const navbar = document.querySelector('.navbar-nav');
        if (navbar && this.shouldAutoRefresh()) {
            const refreshControl = document.createElement('li');
            refreshControl.className = 'nav-item';
            refreshControl.innerHTML = `
                <button id="refreshToggle" class="nav-link btn btn-link" style="border: none; background: none; color: #8b949e;">
                    <i class="bi bi-arrow-clockwise"></i> Auto-Refresh: ON
                </button>
            `;
            
            // Insert before the user dropdown or login button
            const userDropdown = navbar.querySelector('.dropdown') || navbar.querySelector('.btn-primary');
            if (userDropdown) {
                navbar.insertBefore(refreshControl, userDropdown.parentElement);
            } else {
                navbar.appendChild(refreshControl);
            }

            // Add click handler
            document.getElementById('refreshToggle').addEventListener('click', () => {
                this.toggleAutoRefresh();
            });
        }
    }

    startAutoRefresh() {
        const path = window.location.pathname;
        
        if (path === '/' || path === '/tweets/') {
            this.startTweetListRefresh();
        } else if (path.includes('/tweet/')) {
            this.startTweetDetailRefresh();
        }
        
        this.showNotification('Auto-refresh enabled', 'success');
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
                    this.showNotification('New tweets loaded', 'info');
                    
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
                    this.showNotification('Comments updated', 'info');
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

    toggleAutoRefresh() {
        const button = document.getElementById('refreshToggle');
        
        if (this.isEnabled) {
            this.pauseAll();
            this.isEnabled = false;
            button.innerHTML = '<i class="bi bi-pause-circle"></i> Auto-Refresh: OFF';
            button.style.color = '#f85149';
            this.showNotification('Auto-refresh disabled', 'warning');
        } else {
            this.resumeAll();
            this.isEnabled = true;
            button.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Auto-Refresh: ON';
            button.style.color = '#8b949e';
            this.showNotification('Auto-refresh enabled', 'success');
        }
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

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} auto-refresh-notification animate-slide-in`;
        notification.style.cssText = `
            position: fixed;
            top: 140px;
            right: 20px;
            z-index: 9998;
            min-width: 300px;
            padding: 14px 20px;
            font-size: 14px;
            border-radius: 16px;
            opacity: 0;
            transform: translateX(100px);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            background: ${isLight ? 'rgba(255, 255, 255, 0.95)' : 'var(--glass-bg)'};
            backdrop-filter: blur(25px);
            border: 1px solid ${isLight ? 'rgba(226, 232, 240, 0.8)' : 'var(--glass-border)'};
            box-shadow: ${isLight ? '0 8px 32px rgba(15, 23, 42, 0.12)' : '0 8px 32px var(--shadow-color)'};
            font-weight: 500;
        `;
        
        const icons = {
            'info': 'bi-info-circle',
            'success': 'bi-check-circle',
            'warning': 'bi-exclamation-triangle',
            'error': 'bi-x-circle'
        };
        
        const emojis = {
            'info': '🔄',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        };
        
        const theme = document.documentElement.getAttribute('data-bs-theme');
        const isLight = theme === 'light';
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="bi ${icons[type] || icons.info}" style="font-size: 16px; color: var(--accent-color);"></i>
                <span>${emojis[type] || emojis.info} ${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        });
        
        // Add hover effect
        notification.addEventListener('mouseenter', () => {
            notification.style.transform = 'translateX(-5px) scale(1.02)';
        });
        
        notification.addEventListener('mouseleave', () => {
            notification.style.transform = 'translateX(0) scale(1)';
        });
        
        // Auto remove with enhanced animation
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100px) scale(0.9)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 400);
        }, 2500);
    }

    // Manual refresh methods
    async manualRefresh() {
        const path = window.location.pathname;
        
        if (path === '/' || path === '/tweets/') {
            await this.refreshTweetList();
        } else if (path.includes('/tweet/')) {
            await this.refreshTweetDetail();
        }
        
        this.showNotification('Page refreshed manually', 'success');
    }

    // Add manual refresh button
    addManualRefreshButton() {
        const container = document.querySelector('.tweets-container, .index-container, .detail-container');
        if (container) {
            const refreshBtn = document.createElement('button');
            refreshBtn.className = 'btn btn-outline-primary btn-sm manual-refresh-btn';
            
            const theme = document.documentElement.getAttribute('data-bs-theme');
            const isLight = theme === 'light';
            
            refreshBtn.style.cssText = `
                position: fixed;
                bottom: 30px;
                right: 30px;
                z-index: 1000;
                border-radius: 50%;
                width: 65px;
                height: 65px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: ${isLight ? 'rgba(255, 255, 255, 0.95)' : 'var(--glass-bg)'};
                backdrop-filter: blur(25px);
                border: 2px solid var(--accent-color);
                color: var(--accent-color);
                box-shadow: ${isLight ? '0 8px 30px rgba(59, 130, 246, 0.3)' : '0 8px 25px var(--glow-primary)'};
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                font-size: 20px;
                font-weight: 600;
            `;
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i>';
            refreshBtn.title = 'Manual refresh';
            
            // Add hover effects
            refreshBtn.addEventListener('mouseenter', () => {
                refreshBtn.style.transform = 'scale(1.1) rotate(180deg)';
                refreshBtn.style.boxShadow = '0 12px 35px var(--glow-primary)';
            });
            
            refreshBtn.addEventListener('mouseleave', () => {
                refreshBtn.style.transform = 'scale(1) rotate(0deg)';
                refreshBtn.style.boxShadow = '0 8px 25px var(--glow-primary)';
            });
            
            refreshBtn.addEventListener('click', () => {
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i>';
                refreshBtn.style.transform = 'scale(0.95)';
                
                this.manualRefresh().then(() => {
                    refreshBtn.innerHTML = '<i class="bi bi-check-circle"></i>';
                    refreshBtn.style.color = 'var(--success-color)';
                    refreshBtn.style.borderColor = 'var(--success-color)';
                    refreshBtn.style.boxShadow = '0 8px 25px var(--glow-success)';
                    
                    setTimeout(() => {
                        refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i>';
                        refreshBtn.style.color = 'var(--accent-color)';
                        refreshBtn.style.borderColor = 'var(--accent-color)';
                        refreshBtn.style.boxShadow = '0 8px 25px var(--glow-primary)';
                        refreshBtn.style.transform = 'scale(1)';
                    }, 1000);
                });
            });
            
            document.body.appendChild(refreshBtn);
        }
    }
}

// CSS for enhanced animations
const style = document.createElement('style');
style.textContent = `
    .spin {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    @keyframes bounceIn {
        0% {
            opacity: 0;
            transform: scale(0.3) translateX(100px);
        }
        50% {
            opacity: 1;
            transform: scale(1.05) translateX(-10px);
        }
        70% {
            transform: scale(0.9) translateX(5px);
        }
        100% {
            opacity: 1;
            transform: scale(1) translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        0% {
            opacity: 1;
            transform: translateX(0) scale(1);
        }
        100% {
            opacity: 0;
            transform: translateX(100px) scale(0.8);
        }
    }
    
    .auto-refresh-notification {
        animation: bounceIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }
    
    .auto-refresh-notification.removing {
        animation: slideOutRight 0.4s cubic-bezier(0.55, 0.085, 0.68, 0.53);
    }
    
    .manual-refresh-btn {
        animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .manual-refresh-btn:active {
        transform: scale(0.9) !important;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes glow {
        0%, 100% {
            box-shadow: 0 8px 25px var(--glow-primary);
        }
        50% {
            box-shadow: 0 12px 35px var(--glow-primary);
        }
    }
    
    .manual-refresh-btn:hover {
        animation: glow 2s ease-in-out infinite;
    }
`;
document.head.appendChild(style);

// Initialize auto-refresh when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.autoRefresh = new AutoRefresh();
    
    // Add manual refresh button
    window.autoRefresh.addManualRefreshButton();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.autoRefresh) {
        window.autoRefresh.stopAll();
    }
});