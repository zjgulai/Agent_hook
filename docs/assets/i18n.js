(function () {
  const SUPPORTED = ['en', 'zh'];
  const FALLBACK = 'en';

  function detectInitialLang() {
    const saved = localStorage.getItem('i18n-lang');
    if (saved && SUPPORTED.includes(saved)) return saved;
    const browserLang = (navigator.language || '').toLowerCase();
    if (browserLang.startsWith('zh')) return 'zh';
    return FALLBACK;
  }

  function getPageKey() {
    const path = location.pathname;
    const last = path.split('/').filter(Boolean).pop() || 'index';
    return last.replace(/\.html$/, '');
  }

  function applyDict(dict) {
    if (!dict) return;
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      if (dict[key] !== undefined) el.textContent = dict[key];
    });
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      const key = el.dataset.i18nHtml;
      if (dict[key] !== undefined) el.innerHTML = dict[key];
    });
    document.querySelectorAll('[data-i18n-attr]').forEach(el => {
      const spec = el.dataset.i18nAttr;
      const idx = spec.indexOf(':');
      if (idx < 0) return;
      const attr = spec.slice(0, idx);
      const key = spec.slice(idx + 1);
      if (dict[key] !== undefined) el.setAttribute(attr, dict[key]);
    });
  }

  function updateToggleButton(lang) {
    const btn = document.getElementById('lang-toggle');
    if (!btn) return;
    btn.textContent = lang === 'en' ? '中文' : 'EN';
    btn.setAttribute('data-current-lang', lang);
  }

  const currentLang = detectInitialLang();
  const pageKey = getPageKey();
  document.documentElement.lang = currentLang === 'zh' ? 'zh-CN' : 'en';

  if (currentLang === 'zh' && window.I18N_ZH && window.I18N_ZH[pageKey]) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => applyDict(window.I18N_ZH[pageKey]));
    } else {
      applyDict(window.I18N_ZH[pageKey]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => updateToggleButton(currentLang));
  } else {
    updateToggleButton(currentLang);
  }

  window.i18nToggle = function () {
    const now = document.documentElement.lang.startsWith('zh') ? 'zh' : 'en';
    const next = now === 'en' ? 'zh' : 'en';
    localStorage.setItem('i18n-lang', next);
    location.reload();
  };
})();
