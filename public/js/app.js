// Aviation Traceability System - Public JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('🛩️ Aviation Traceability System - Public Files Loaded');
    
    // Initialize application
    initializeApp();
    
    // Add smooth scrolling for navigation
    addSmoothScrolling();
    
    // Add interactive features
    addInteractiveFeatures();
    
    // Add system status check
    checkSystemStatus();
});

function initializeApp() {
    // Add loading animation
    const sections = document.querySelectorAll('.content section');
    sections.forEach((section, index) => {
        section.style.animationDelay = `${index * 0.1}s`;
    });
    
    // Add click handlers for feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

function addSmoothScrolling() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function addInteractiveFeatures() {
    // Add hover effects to code examples
    const codeExamples = document.querySelectorAll('.example code');
    codeExamples.forEach(code => {
        code.addEventListener('click', function() {
            // Copy to clipboard
            navigator.clipboard.writeText(this.textContent).then(() => {
                showNotification('URL copied to clipboard!', 'success');
            }).catch(() => {
                showNotification('Failed to copy URL', 'error');
            });
        });
        
        // Add tooltip
        code.title = 'Click to copy URL';
        code.style.cursor = 'pointer';
    });
    
    // Add file structure interactivity
    const folders = document.querySelectorAll('.folder');
    folders.forEach(folder => {
        const folderContents = folder.querySelector('.folder-contents');
        if (folderContents) {
            folder.addEventListener('click', function(e) {
                if (e.target === this || e.target.classList.contains('folder-icon')) {
                    folderContents.style.display = 
                        folderContents.style.display === 'none' ? 'block' : 'none';
                }
            });
        }
    });
}

function checkSystemStatus() {
    // Check if main application is running
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'healthy') {
                addStatusIndicator('System Online', 'success');
            } else {
                addStatusIndicator('System Issues', 'warning');
            }
        })
        .catch(() => {
            addStatusIndicator('System Offline', 'error');
        });
}

function addStatusIndicator(message, type) {
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-indicator ${type}`;
    statusDiv.innerHTML = `
        <span class="status-icon">${getStatusIcon(type)}</span>
        <span class="status-text">${message}</span>
    `;
    
    // Add to header
    const header = document.querySelector('.header');
    if (header) {
        header.appendChild(statusDiv);
    }
    
    // Add CSS for status indicator
    addStatusStyles();
}

function getStatusIcon(type) {
    switch(type) {
        case 'success': return '✅';
        case 'warning': return '⚠️';
        case 'error': return '❌';
        default: return 'ℹ️';
    }
}

function addStatusStyles() {
    if (document.getElementById('status-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'status-styles';
    style.textContent = `
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            margin-top: 1rem;
            animation: slideIn 0.3s ease;
        }
        
        .status-indicator.success {
            background: rgba(40, 167, 69, 0.2);
            color: #155724;
            border: 1px solid rgba(40, 167, 69, 0.3);
        }
        
        .status-indicator.warning {
            background: rgba(255, 193, 7, 0.2);
            color: #856404;
            border: 1px solid rgba(255, 193, 7, 0.3);
        }
        
        .status-indicator.error {
            background: rgba(220, 53, 69, 0.2);
            color: #721c24;
            border: 1px solid rgba(220, 53, 69, 0.3);
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${getStatusIcon(type)}</span>
        <span class="notification-text">${message}</span>
    `;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Add notification styles
    addNotificationStyles();
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function addNotificationStyles() {
    if (document.getElementById('notification-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 1000;
            animation: slideInRight 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .notification.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .notification.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .notification.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
    `;
    document.head.appendChild(style);
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Export functions for external use
window.AviationTraceability = {
    showNotification,
    formatFileSize,
    formatDate,
    // checkSystemStatus
};

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search (if implemented)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        showNotification('Search functionality coming soon!', 'info');
    }
    
    // Escape to close any modals or notifications
    if (e.key === 'Escape') {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(notification => notification.remove());
    }
});

// Add performance monitoring
window.addEventListener('load', function() {
    const loadTime = performance.now();
    console.log(`🚀 Page loaded in ${Math.round(loadTime)}ms`);
    
    // Add load time to footer
    const footer = document.querySelector('.footer');
    if (footer) {
        const loadTimeElement = document.createElement('div');
        loadTimeElement.className = 'load-time';
        loadTimeElement.innerHTML = `Page loaded in ${Math.round(loadTime)}ms`;
        loadTimeElement.style.cssText = `
            font-size: 0.8rem;
            color: #adb5bd;
            margin-top: 0.5rem;
        `;
        footer.appendChild(loadTimeElement);
    }
}); 