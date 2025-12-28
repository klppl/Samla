(function() {
    // Check local storage or system preference
    const getPreferredTheme = () => {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    };

    const setTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update button icon if it exists
        const btn = document.getElementById('theme-toggle-btn');
        if (btn) {
            btn.textContent = theme === 'light' ? '🌙' : '☀️';
        }
    };

    // Apply theme immediately to prevent FOUC
    const currentTheme = getPreferredTheme();
    setTheme(currentTheme);

    // Expose toggle function globally
    window.toggleTheme = () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'light' ? 'dark' : 'light';
        setTheme(next);
    };

    // Initialize button on load
    document.addEventListener('DOMContentLoaded', () => {
        const btn = document.getElementById('theme-toggle-btn');
        if (btn) {
            btn.addEventListener('click', window.toggleTheme);
            // Set initial icon
            btn.textContent = document.documentElement.getAttribute('data-theme') === 'light' ? '🌙' : '☀️';
        }
    });
})();
