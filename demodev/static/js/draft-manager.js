/**
 * Draft Manager - Handles auto-save and draft restoration for tweets
 * Features:
 * - Auto-save draft every 30 seconds
 * - Restore draft on page load
 * - Clear draft after successful tweet publication
 * - Manual draft save/clear
 */

class DraftManager {
    constructor(options = {}) {
        this.autoSaveInterval = options.autoSaveInterval || 30000; // 30 seconds
        this.formSelector = options.formSelector || 'form[method="post"]';
        this.textareaSelector = options.textareaSelector || 'textarea[name="text"]';
        this.autoSaveTimer = null;
        this.isDirty = false;
        this.isInitialized = false;
        
        this.init();
    }
    
    /**
     * Initialize the draft manager
     */
    init() {
        if (this.isInitialized) return;
        
        const form = document.querySelector(this.formSelector);
        const textarea = document.querySelector(this.textareaSelector);
        
        if (!form || !textarea) {
            console.warn('DraftManager: Form or textarea not found');
            return;
        }
        
        // Mark form as dirty when content changes
        textarea.addEventListener('input', () => {
            this.isDirty = true;
            this.resetAutoSaveTimer();
        });
        
        // Clear draft on successful form submission
        form.addEventListener('submit', (e) => {
            // Only clear if form is valid (will be submitted)
            // We'll clear after successful submission via the response
            this.markFormSubmitting();
        });
        
        // Start auto-save timer
        this.startAutoSaveTimer();
        
        // Check for existing draft on page load
        this.checkAndRestoreDraft();
        
        this.isInitialized = true;
    }
    
    /**
     * Start the auto-save timer
     */
    startAutoSaveTimer() {
        this.autoSaveTimer = setInterval(() => {
            if (this.isDirty) {
                this.autosaveDraft();
            }
        }, this.autoSaveInterval);
    }
    
    /**
     * Reset the auto-save timer
     */
    resetAutoSaveTimer() {
        // Timer continues running, just mark as dirty
    }
    
    /**
     * Auto-save the current draft
     */
    autosaveDraft() {
        const textarea = document.querySelector(this.textareaSelector);
        if (!textarea) return;
        
        const content = textarea.value.trim();
        if (!content) return;
        
        const mediaIds = this.getSelectedMediaIds();
        
        this.saveDraft(content, mediaIds, true); // true = silent save
    }
    
    /**
     * Save draft to server
     */
    saveDraft(content, mediaIds = [], silent = false) {
        if (!content.trim()) {
            if (!silent) {
                this.showNotification('Draft content cannot be empty', 'warning');
            }
            return;
        }
        
        const csrfToken = this.getCsrfToken();
        
        fetch('/draft/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                content: content,
                media_ids: mediaIds
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.isDirty = false;
                if (!silent) {
                    this.showNotification('Draft saved successfully', 'success');
                }
            } else {
                if (!silent) {
                    this.showNotification(data.error || 'Failed to save draft', 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error saving draft:', error);
            if (!silent) {
                this.showNotification('Error saving draft', 'error');
            }
        });
    }
    
    /**
     * Check for existing draft and prompt to restore
     */
    checkAndRestoreDraft() {
        const csrfToken = this.getCsrfToken();
        
        fetch('/draft/get/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.draft && data.draft.content) {
                this.showRestorePrompt(data.draft);
            }
        })
        .catch(error => {
            console.error('Error checking for draft:', error);
        });
    }
    
    /**
     * Show prompt to restore draft
     */
    showRestorePrompt(draft) {
        const textarea = document.querySelector(this.textareaSelector);
        if (!textarea) return;
        
        // Check if textarea already has content
        if (textarea.value.trim()) {
            return; // Don't prompt if user already has content
        }
        
        // Create a modal/prompt for draft restoration
        const promptDiv = document.createElement('div');
        promptDiv.className = 'draft-restore-prompt alert alert-info alert-dismissible fade show';
        promptDiv.setAttribute('role', 'alert');
        promptDiv.innerHTML = `
            <strong>Draft Found!</strong> You have a saved draft from ${new Date(draft.updated_at).toLocaleString()}.
            <div class="mt-2">
                <button type="button" class="btn btn-sm btn-primary" id="restore-draft-btn">
                    <i class="bi bi-arrow-counterclockwise"></i> Restore Draft
                </button>
                <button type="button" class="btn btn-sm btn-secondary" id="discard-draft-btn">
                    <i class="bi bi-trash"></i> Discard
                </button>
            </div>
        `;
        
        // Insert before the form
        const form = document.querySelector(this.formSelector);
        if (form) {
            form.parentNode.insertBefore(promptDiv, form);
        }
        
        // Handle restore button
        document.getElementById('restore-draft-btn').addEventListener('click', () => {
            this.restoreDraft(draft);
            promptDiv.remove();
        });
        
        // Handle discard button
        document.getElementById('discard-draft-btn').addEventListener('click', () => {
            this.clearDraft();
            promptDiv.remove();
        });
    }
    
    /**
     * Restore draft content to form
     */
    restoreDraft(draft) {
        const textarea = document.querySelector(this.textareaSelector);
        if (!textarea) return;
        
        textarea.value = draft.content;
        this.isDirty = false;
        
        // Restore media if available
        if (draft.media && draft.media.length > 0) {
            this.restoreMediaToForm(draft.media);
        }
        
        this.showNotification('Draft restored successfully', 'success');
    }
    
    /**
     * Restore media to form
     */
    restoreMediaToForm(mediaList) {
        // This would need to be implemented based on your media upload UI
        // For now, we'll just log it
        console.log('Restoring media:', mediaList);
        
        // Trigger a custom event that media upload handler can listen to
        const event = new CustomEvent('draftMediaRestore', { detail: { media: mediaList } });
        document.dispatchEvent(event);
    }
    
    /**
     * Clear draft from server
     */
    clearDraft() {
        const csrfToken = this.getCsrfToken();
        
        fetch('/draft/clear/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.isDirty = false;
                this.showNotification('Draft cleared', 'info');
            }
        })
        .catch(error => {
            console.error('Error clearing draft:', error);
        });
    }
    
    /**
     * Mark form as submitting (will clear draft after success)
     */
    markFormSubmitting() {
        // This will be handled by the form submission response
        // We'll clear the draft after successful tweet creation
    }
    
    /**
     * Get selected media IDs from the form
     */
    getSelectedMediaIds() {
        // This would need to be implemented based on your media upload UI
        // For now, return empty array
        const mediaIds = [];
        
        // Look for hidden inputs or data attributes that store media IDs
        const mediaInputs = document.querySelectorAll('input[name="media_ids[]"]');
        mediaInputs.forEach(input => {
            if (input.value) {
                mediaIds.push(parseInt(input.value));
            }
        });
        
        return mediaIds;
    }
    
    /**
     * Get CSRF token from page
     */
    getCsrfToken() {
        const name = 'csrftoken';
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
        
        // Also check for token in meta tag
        if (!cookieValue) {
            const token = document.querySelector('[name=csrfmiddlewaretoken]');
            if (token) {
                cookieValue = token.value;
            }
        }
        
        return cookieValue;
    }
    
    /**
     * Show notification message
     */
    showNotification(message, type = 'info') {
        // Create a simple notification
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Insert at the top of the page
        const container = document.querySelector('.form-container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
    
    /**
     * Destroy the draft manager
     */
    destroy() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
        }
        this.isInitialized = false;
    }
}

// Initialize draft manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on tweet creation/edit pages
    const form = document.querySelector('form[method="post"]');
    const textarea = document.querySelector('textarea[name="text"]');
    
    if (form && textarea) {
        window.draftManager = new DraftManager({
            autoSaveInterval: 30000, // 30 seconds
            formSelector: 'form[method="post"]',
            textareaSelector: 'textarea[name="text"]'
        });
    }
});
