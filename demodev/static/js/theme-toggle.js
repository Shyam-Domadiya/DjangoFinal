// Theme Toggle functionality
class ThemeToggle {
    constructor() {
        this.htmlRoot = document.getElementById('html-root');
        this.toggleButton = document.getElementById('themeToggle');
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        
        this.init();
    }
    
    init() {
        // Set initial theme
        this.setTheme(this.currentTheme);
        
        // Add click listener
        if (this.toggleButton) {
            this.toggleButton.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }
    
    setTheme(theme) {
        this.currentTheme = theme;
        this.htmlRoot.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update button icon and text
        if (this.toggleButton) {
            const icon = this.toggleButton.querySelector('i');
            if (theme === 'dark') {
                icon.className = 'bi bi-sun-fill';
                this.toggleButton.title = 'Switch to light theme';
            } else {
                icon.className = 'bi bi-moon-fill';
                this.toggleButton.title = 'Switch to dark theme';
            }
        }
        
        // Show notification (only after initial load)
        if (this.hasInitialized) {
            this.showThemeNotification(theme);
        }
        this.hasInitialized = true;
    }
    
    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
    
    showThemeNotification(theme) {
        // Create notification
        const notification = document.createElement('div');
        notification.className = 'alert alert-info theme-notification animate-slide-in';
        notification.style.cssText = `
            position: fixed;
            top: 90px;
            right: 20px;
            z-index: 9999;
            min-width: 250px;
            padding: 12px 20px;
            font-size: 14px;
            border-radius: 12px;
            opacity: 0;
            transform: translateX(100px);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            box-shadow: 0 8px 32px var(--shadow-color);
            font-weight: 500;
        `;
        
        const themeName = theme === 'dark' ? 'Dark' : 'Light';
        const icon = theme === 'dark' ? 'bi-moon-stars' : 'bi-sun';
        const emoji = theme === 'dark' ? '🌙' : '☀️';
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="bi ${icon}" style="font-size: 18px; color: var(--accent-color);"></i>
                <span>${emoji} ${themeName} theme activated</span>
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
        }, 3000);
    }
}

// Initialize theme toggle when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeToggle = new ThemeToggle();
});