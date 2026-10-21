// 只在启用 JavaScript 时出现的控件：主题切换、演示引导与重置。
(() => {
  'use strict';
  document.querySelectorAll('[data-tour], [data-demo-go="reset"], [data-theme-toggle]').forEach(el => { el.hidden = false; });

  const toggle = document.querySelector('[data-theme-toggle]');
  const names = { system: '跟随系统', light: '浅色', dark: '深色' };
  const order = ['system', 'light', 'dark'];
  let current = document.documentElement.dataset.theme || 'system';
  const show = () => { toggle.textContent = '主题：' + names[current]; };
  show();
  toggle.addEventListener('click', () => {
    current = order[(order.indexOf(current) + 1) % order.length];
    if (current === 'system') delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = current;
    try { if (current === 'system') localStorage.removeItem('enchanted-theme'); else localStorage.setItem('enchanted-theme', current); } catch (error) { /* 无法保存时只在本次浏览中生效 */ }
    show();
  });
})();
