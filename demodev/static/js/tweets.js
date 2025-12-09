// AJAX Tweet functionality
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Delete tweet via AJAX
function deleteTweet(tweetId) {
    if (!confirm('Are you sure you want to delete this tweet?')) {
        return false;
    }
    
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/${tweetId}/delete`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove tweet from DOM
            const tweetCard = document.querySelector(`[data-tweet-id="${tweetId}"]`);
            if (tweetCard) {
                tweetCard.style.transition = 'opacity 0.3s';
                tweetCard.style.opacity = '0';
                setTimeout(() => {
                    tweetCard.remove();
                    
                    // Check if there are no more tweets
                    const tweetsGrid = document.querySelector('.tweets-grid, .index-container');
                    if (tweetsGrid && tweetsGrid.querySelectorAll('.tweet-card').length === 0) {
                        showEmptyState(tweetsGrid);
                    }
                }, 300);
            }
            
            showMessage('Tweet deleted successfully!', 'success');
        } else {
            showMessage(data.error || 'Failed to delete tweet', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('An error occurred', 'error');
    });
    
    return false;
}

// Show empty state
function showEmptyState(container) {
    const emptyHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">
                <i class="bi bi-inbox"></i>
            </div>
            <p class="empty-state-text">No tweets yet. Start sharing your thoughts!</p>
            <a href="/create/" class="empty-state-link">
                <i class="bi bi-plus-circle"></i> Create Your First Tweet
            </a>
        </div>
    `;
    container.innerHTML = emptyHTML;
}

// Show message notification
function showMessage(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '80px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// Auto-refresh tweets (optional - can be enabled)
function enableAutoRefresh(intervalSeconds = 30) {
    setInterval(() => {
        refreshTweets();
    }, intervalSeconds * 1000);
}

// Refresh tweets without page reload
function refreshTweets() {
    const tweetsGrid = document.querySelector('.tweets-grid');
    if (!tweetsGrid) return;
    
    fetch(window.location.href, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newTweetsGrid = doc.querySelector('.tweets-grid');
        
        if (newTweetsGrid) {
            tweetsGrid.innerHTML = newTweetsGrid.innerHTML;
        }
    })
    .catch(error => {
        console.error('Error refreshing tweets:', error);
    });
}
