// AJAX Comment functionality
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

// Add comment via AJAX
function addComment(tweetId, form) {
    const csrftoken = getCookie('csrftoken');
    const commentText = form.querySelector('textarea[name="comment_text"]').value;
    
    if (!commentText.trim()) {
        alert('Please enter a comment');
        return false;
    }
    
    fetch(`/tweet/${tweetId}/comment/add/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            comment_text: commentText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear the textarea
            form.querySelector('textarea[name="comment_text"]').value = '';
            
            // Add new comment to the list
            const commentsList = document.querySelector('.comments-list');
            const emptyState = document.querySelector('.empty-comments');
            
            if (emptyState) {
                emptyState.remove();
            }
            
            const newComment = createCommentElement(data.comment);
            commentsList.insertAdjacentHTML('afterbegin', newComment);
            
            // Update comment count
            updateCommentCount(tweetId, data.comment_count);
            
            // Show success message
            showMessage('Comment added successfully!', 'success');
        } else {
            showMessage(data.error || 'Failed to add comment', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('An error occurred', 'error');
    });
    
    return false; // Prevent form submission
}

// Delete comment via AJAX
function deleteComment(commentId, tweetId) {
    if (!confirm('Are you sure you want to delete this comment?')) {
        return;
    }
    
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/comment/delete/${commentId}/`, {
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
            // Remove comment from DOM
            const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
            if (commentElement) {
                commentElement.remove();
            }
            
            // Update comment count
            updateCommentCount(tweetId, data.comment_count);
            
            // Show empty state if no comments
            const commentsList = document.querySelector('.comments-list');
            if (commentsList && commentsList.children.length === 0) {
                commentsList.innerHTML = `
                    <div class="empty-comments">
                        <i class="bi bi-chat" style="font-size: 48px;"></i>
                        <p>No comments yet. Be the first to comment!</p>
                    </div>
                `;
            }
            
            showMessage('Comment deleted successfully!', 'success');
        } else {
            showMessage(data.error || 'Failed to delete comment', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('An error occurred', 'error');
    });
}

// Helper function to create comment HTML
function createCommentElement(comment) {
    const timeAgo = comment.time_ago || 'just now';
    const canDelete = comment.can_delete ? `
        <button onclick="deleteComment(${comment.id}, ${comment.tweet_id})" class="comment-delete">
            <i class="bi bi-trash"></i> Delete
        </button>
    ` : '';
    
    return `
        <div class="comment-card" data-comment-id="${comment.id}">
            <div class="comment-header">
                <div class="comment-user">
                    <div class="comment-avatar">
                        ${comment.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <div class="comment-username">${comment.username}</div>
                        <div class="comment-time">${timeAgo}</div>
                    </div>
                </div>
                ${canDelete}
            </div>
            <div class="comment-text">
                ${comment.text}
            </div>
        </div>
    `;
}

// Update comment count in UI
function updateCommentCount(tweetId, count) {
    const countElements = document.querySelectorAll(`[data-tweet-id="${tweetId}"] .comment-count, .tweet-meta .bi-chat + span`);
    countElements.forEach(el => {
        const text = count === 1 ? 'comment' : 'comments';
        if (el.classList.contains('comment-count')) {
            el.textContent = count;
        } else {
            el.textContent = ` ${count} ${text}`;
        }
    });
    
    // Update header count
    const headerCount = document.querySelector('.comments-header');
    if (headerCount) {
        headerCount.innerHTML = `<i class="bi bi-chat-dots"></i> Comments (${count})`;
    }
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
