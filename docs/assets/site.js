// 只在启用 JavaScript 时出现的控件：主题切换。导览的控件由 tour.js 显示。
(() => {
  'use strict';
  document.querySelectorAll('[data-theme-toggle]').forEach(el => { el.hidden = false; });

  const toggle = document.querySelector('[data-theme-toggle]');
  const names = { system: '跟随系统', light: '浅色', dark: '深色' };
  const order = ['system', 'light', 'dark'];
  let current = document.documentElement.dataset.theme || 'system';
  const systemTheme = matchMedia('(prefers-color-scheme: dark)');
  const updateIcon = () => {
    const dark = current === 'dark' || (current === 'system' && systemTheme.matches);
    document.querySelectorAll('link[rel="icon"]').forEach(icon => icon.remove());
    const icon = document.createElement('link');
    icon.rel = 'icon'; icon.type = 'image/png';
    icon.href = './assets/brand/logo-on-' + (dark ? 'dark' : 'light') + '.png';
    document.head.append(icon);
  };
  const show = () => { toggle.textContent = '主题：' + names[current]; updateIcon(); };
  systemTheme.addEventListener('change', updateIcon);
  show();
  toggle.addEventListener('click', () => {
    current = order[(order.indexOf(current) + 1) % order.length];
    if (current === 'system') delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = current;
    try { if (current === 'system') localStorage.removeItem('enchanted-theme'); else localStorage.setItem('enchanted-theme', current); } catch (error) { /* 无法保存时只在本次浏览中生效 */ }
    show();
  });
})();
