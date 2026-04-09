/**
 * AgriBuddy Global Theme Management
 * Handles dark/light mode switching and cross-tab synchronization.
 */

// Function to toggle the theme
function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    const isLight = html.getAttribute('data-theme') === 'light';
    const newTheme = isLight ? 'dark' : 'light';
    
    if (isLight) {
        html.removeAttribute('data-theme');
        html.classList.add('dark');
        if (icon) icon.className = 'fas fa-moon';
        localStorage.setItem('agribuddy-theme', 'dark');
    } else {
        html.setAttribute('data-theme', 'light');
        html.classList.remove('dark');
        if (icon) icon.className = 'fas fa-sun';
        localStorage.setItem('agribuddy-theme', 'light');
    }
    
    // Dispatch instant event for professional reactive components (like charts)
    window.dispatchEvent(new CustomEvent('agribuddyThemeChanged', { 
        detail: { theme: newTheme } 
    }));
}

// Function to apply the saved theme
function applyTheme() {
    const theme = localStorage.getItem('agribuddy-theme');
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    
    if (theme === 'light') {
        html.setAttribute('data-theme', 'light');
        html.classList.remove('dark');
        if (icon) icon.className = 'fas fa-sun';
    } else {
        html.removeAttribute('data-theme');
        html.classList.add('dark');
        if (icon) icon.className = 'fas fa-moon';
    }
}

// Global Sidebar Functions
function openSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.add('active');
    if (backdrop) backdrop.classList.add('active');
}

function closeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (sidebar) sidebar.classList.remove('active');
    if (backdrop) backdrop.classList.remove('active');
}

// Global Logout Function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}

// Listen for storage changes to sync theme across tabs
window.addEventListener('storage', (event) => {
    if (event.key === 'agribuddy-theme') {
        applyTheme();
    }
});

// Setup Global Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    applyTheme();
    
    // Auto-setup sidebar toggles
    document.querySelectorAll('.sidebar-toggle').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            openSidebar();
        });
    });
    
    const backdrop = document.getElementById('sidebar-backdrop');
    if (backdrop) {
        backdrop.addEventListener('click', closeSidebar);
    }
    
    // Close sidebar on nav click (mobile)
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) closeSidebar();
        });
    });
});
