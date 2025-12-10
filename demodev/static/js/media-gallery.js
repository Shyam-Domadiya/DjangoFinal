/**
 * Media Gallery Management
 * Handles loading, displaying, and managing media files in a gallery view
 */

let currentMediaId = null;

/**
 * Load and display user's media gallery
 */
function loadMediaGallery() {
    const container = document.getElementById('media-gallery-container');
    if (!container) return;

    // Show loading state
    container.innerHTML = '<div id="media-gallery-loading" style="text-align: center; padding: 40px;"><p style="color: var(--text-secondary);">Loading media...</p></div>';

    // Fetch user's media
    fetch('/media/user/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.media && data.media.length > 0) {
            renderMediaGallery(data.media);
        } else {
            renderEmptyMediaState();
        }
    })
    .catch(error => {
        console.error('Error loading media gallery:', error);
        container.innerHTML = '<div class="empty-media-state"><div class="empty-media-state-icon"><i class="bi bi-exclamation-triangle"></i></div><p class="empty-media-state-text">Error loading media gallery</p></div>';
    });
}

/**
 * Render media gallery items
 */
function renderMediaGallery(mediaItems) {
    const container = document.getElementById('media-gallery-container');
    
    let html = '';
    mediaItems.forEach(media => {
        html += `
            <div class="media-gallery-item" onclick="openMediaLightbox(${media.id}, '${media.thumbnail_url}')">
                <img src="${media.thumbnail_url}" alt="Media" loading="lazy">
                <div class="media-gallery-item-overlay">
                    <button class="media-gallery-item-action" onclick="event.stopPropagation(); openMediaLightbox(${media.id}, '${media.thumbnail_url}')">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="media-gallery-item-action delete" onclick="event.stopPropagation(); deleteMediaConfirm(${media.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

/**
 * Render empty media state
 */
function renderEmptyMediaState() {
    const container = document.getElementById('media-gallery-container');
    container.innerHTML = `
        <div class="empty-media-state" style="grid-column: 1 / -1;">
            <div class="empty-media-state-icon">
                <i class="bi bi-image"></i>
            </div>
            <p class="empty-media-state-text">No media uploaded yet. Start by uploading images to your tweets!</p>
        </div>
    `;
}

/**
 * Open media in lightbox with associated tweets
 */
function openMediaLightbox(mediaId, imageUrl) {
    currentMediaId = mediaId;
    
    const lightbox = document.getElementById('media-lightbox');
    const lightboxImage = document.getElementById('lightbox-image');
    const lightboxTitle = document.getElementById('lightbox-title');
    const lightboxTweets = document.getElementById('lightbox-tweets');
    
    // Set image
    lightboxImage.src = imageUrl;
    lightboxTitle.textContent = 'Media Details';
    
    // Fetch associated tweets
    fetch(`/media/${mediaId}/tweets/`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.tweets && data.tweets.length > 0) {
            let tweetsHtml = '';
            data.tweets.forEach(tweet => {
                tweetsHtml += `
                    <div class="lightbox-tweet-item" onclick="window.location.href='/tweet/${tweet.id}/'">
                        <p class="lightbox-tweet-text">${escapeHtml(tweet.text)}</p>
                        <small style="color: var(--text-secondary);">by @${escapeHtml(tweet.username)}</small>
                    </div>
                `;
            });
            lightboxTweets.innerHTML = tweetsHtml;
        } else {
            lightboxTweets.innerHTML = '<p style="color: var(--text-secondary);">No tweets associated with this media</p>';
        }
    })
    .catch(error => {
        console.error('Error loading associated tweets:', error);
        lightboxTweets.innerHTML = '<p style="color: var(--text-secondary);">Error loading associated tweets</p>';
    });
    
    // Show lightbox
    lightbox.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

/**
 * Close media lightbox
 */
function closeMediaLightbox() {
    const lightbox = document.getElementById('media-lightbox');
    lightbox.style.display = 'none';
    document.body.style.overflow = 'auto';
    currentMediaId = null;
}

/**
 * Delete media with confirmation
 */
function deleteMediaConfirm(mediaId) {
    if (confirm('Are you sure you want to delete this media? This will remove it from all associated tweets.')) {
        deleteMedia(mediaId);
    }
}

/**
 * Delete media from lightbox
 */
function deleteMediaFromLightbox() {
    if (currentMediaId && confirm('Are you sure you want to delete this media? This will remove it from all associated tweets.')) {
        deleteMedia(currentMediaId);
        closeMediaLightbox();
    }
}

/**
 * Delete media file
 */
function deleteMedia(mediaId) {
    fetch(`/media/${mediaId}/delete/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification('Media deleted successfully', 'success');
            // Reload gallery
            loadMediaGallery();
        } else {
            showNotification('Error deleting media: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error deleting media:', error);
        showNotification('Error deleting media', 'error');
    });
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? 'var(--success-color)' : type === 'error' ? 'var(--danger-color)' : 'var(--accent-color)'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        z-index: 2000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Close lightbox when clicking overlay
 */
document.addEventListener('DOMContentLoaded', function() {
    const lightbox = document.getElementById('media-lightbox');
    if (lightbox) {
        lightbox.addEventListener('click', function(e) {
            if (e.target === lightbox || e.target.classList.contains('lightbox-overlay')) {
                closeMediaLightbox();
            }
        });
    }
    
    // Load media gallery if on profile page
    if (document.getElementById('media-gallery-container')) {
        loadMediaGallery();
    }
});

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
