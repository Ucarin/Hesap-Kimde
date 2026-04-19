// Theme and Language Preference Management

function applyTheme(theme) {
    const logo = document.getElementById('main-logo');
    const favicon = document.getElementById('favicon');
    if (theme === 'light') {
        document.body.classList.add('light-theme');
        if (logo) logo.src = '/logo-light';
        if (favicon) favicon.href = '/logo-light';
    } else {
        document.body.classList.remove('light-theme');
        if (logo) logo.src = '/logo-dark';
        if (favicon) favicon.href = '/logo-dark';
    }
    localStorage.setItem('theme', theme);
    updateThemeToggleIcon(theme);
}

function updateThemeToggleIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.textContent = theme === 'light' ? '🌙' : '☀️';
    }
}

function toggleTheme() {
    const currentTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
    const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(nextTheme);
}

function setLanguage(lang) {
    if (!translations[lang]) lang = 'tr';
    localStorage.setItem('lang', lang);
    
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = translations[lang][key];
            } else {
                el.innerHTML = translations[lang][key];
            }
        }
    });

    const langSelect = document.getElementById('lang-select');
    if (langSelect) langSelect.value = lang;
    
    // Update active flag UI
    const flags = { 'tr': '🇹🇷', 'en': '🇺🇸', 'es': '🇪🇸' };
    const currentFlag = document.getElementById('current-lang-flag');
    const currentText = document.getElementById('current-lang-text');
    
    if (currentFlag) currentFlag.textContent = flags[lang];
    if (currentText) currentText.textContent = lang.toUpperCase();

    // Close all dropdowns
    document.querySelectorAll('.custom-dropdown').forEach(d => {
        d.classList.remove('active');
        // Highlight active button in menu
        d.querySelectorAll('.dropdown-menu button').forEach(btn => {
            const onClickAttr = btn.getAttribute('onclick');
            if (onClickAttr && onClickAttr.includes(`'${lang}'`)) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    });

    document.documentElement.lang = lang;
}

function initPreferences() {
    // Theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    } else {
        const prefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
        applyTheme(prefersLight ? 'light' : 'dark');
    }

    // Language
    const savedLang = localStorage.getItem('lang');
    if (savedLang) {
        setLanguage(savedLang);
    } else {
        const browserLang = navigator.language.split('-')[0];
        setLanguage(['tr', 'en', 'es'].includes(browserLang) ? browserLang : 'tr');
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
            applyTheme(e.matches ? 'light' : 'dark');
        }
    });
}

function toggleDropdown() {
    const dropdown = document.getElementById('lang-dropdown');
    if (dropdown) dropdown.classList.toggle('active');
}

// Close dropdown when clicking outside
document.addEventListener('click', e => {
    if (!e.target.closest('.custom-dropdown')) {
        document.querySelectorAll('.custom-dropdown').forEach(d => d.classList.remove('active'));
    }
});

// Global functions for UI events
window.handleThemeToggle = toggleTheme;
window.handleLangChange = (e) => setLanguage(e.target.value);
window.toggleDropdown = toggleDropdown;

document.addEventListener('DOMContentLoaded', initPreferences);
