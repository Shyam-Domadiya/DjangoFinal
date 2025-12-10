/**
 * Pin Tweet Functionality
 * Handles pinning and unpinning tweets to user profile
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle pin button clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('pin-btn')) {
            handlePinClick(e);
        }
        if (e.target.classList.contains('unpin-btn')) {
            handleUnpinClick(e);
        }
    });
});

function handlePinClick(e) {
    const tweetId = e.target.dataset.tweetId;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                      document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    
    fetch(`/tweet/${tweetId}/pin/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI
            const btn = e.target;
            btn.classList.remove('pin-btn');
            btn.classList.add('unpin-btn');
            btn.textContent = 'Unpin';
            btn.title = 'Unpin from profile';
            
            // Show success message
            showNotification('Tweet pinned to your profile', 'success');
        } else {
            showNotification(data.error || 'Failed to pin tweet', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while pinning the tweet', 'error');
    });
}

function handleUnpinClick(e) {
    const tweetId = e.target.dataset.tweetId;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                      document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    
    fetch(`/tweet/${tweetId}/unpin/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI
            const btn = e.target;
            btn.classList.remove('unpin-btn');
            btn.classList.add('pin-btn');
            btn.textContent = 'Pin';
            btn.title = 'Pin to profile';
            
            // Show success message
            showNotification('Tweet unpinned from your profile', 'success');
        } else {
            showNotification(data.error || 'Failed to unpin tweet', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred while unpinning the tweet', 'error');
    });
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background-color: ${type === 'success' ? '#4CAF50' : '#f44336'};
        color: white;
        border-radius: 4px;
        z-index: 1000;
        animation: slideIn 0.3s ease-in-out;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
