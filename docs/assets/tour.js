// 第二屏的分步导览：演示窗口贴满一屏时，滚轮每滚一下切一步，方向键、翻页键、空格、触摸滑动和圆点也能切。
// 第一步再往上回到首屏，最后一步再往下进入下载说明。窗口里需要滚动的区域先滚它自己，滚到头再切步。
(() => {
  'use strict';
  const tour = document.querySelector('.tour');
  const demo = window.EnchantedDemo;
  if (!tour || !demo) return;
  const steps = [...tour.querySelectorAll('[data-tour-steps] > li')];
  const dots = tour.querySelector('[data-tour-dots]');
  const stage = tour.querySelector('[data-tour-stage]'), frame = tour.querySelector('[data-tour-frame]');
  const wb = document.getElementById('wb-demo');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let index = 0;
  tour.classList.add('is-live');
  tour.querySelectorAll('[data-tour-dots], [data-tour-hint], [data-tour-reset]').forEach(el => { el.hidden = false; });
  tour.querySelector('[data-tour-total]').textContent = steps.length;
  dots.innerHTML = steps.map((step, i) => `<button type="button" data-dot="${i}" aria-label="第 ${i + 1} 步：${step.querySelector('h3').textContent}"></button>`).join('');

  function show(next) {
    index = Math.max(0, Math.min(steps.length - 1, next));
    steps.forEach((step, i) => step.classList.toggle('is-current', i === index));
    dots.querySelectorAll('button').forEach((dot, i) => dot.setAttribute('aria-current', i === index ? 'step' : 'false'));
    tour.querySelector('[data-tour-index]').textContent = index + 1;
    demo.go(steps[index].dataset.scene);
  }

  // 窗口按 1040×760 还原，按舞台大小整体缩放。
  function fit() {
    const scale = Math.min(1, stage.clientWidth / wb.offsetWidth, (stage.clientHeight - 28) / wb.offsetHeight);
    frame.style.width = wb.offsetWidth * scale + 'px';
    frame.style.height = wb.offsetHeight * scale + 'px';
    wb.style.transform = `scale(${scale})`;
  }
  new ResizeObserver(fit).observe(stage);

  const top = () => tour.getBoundingClientRect().top;
  const pinned = () => Math.abs(top()) < 2;
  // 离顶部只差几十像素（惯性、浏览器取整）也算在第二屏里：先贴回去，再按换步处理。
  const near = () => Math.abs(top()) < 48;
  const repin = () => { if (!pinned()) window.scrollTo({ top: window.scrollY + top(), behavior: 'auto' }); };
  let snapping = false;
  function scrollToY(y, then) {
    snapping = true;
    window.scrollTo({ top: y, behavior: reduced.matches ? 'auto' : 'smooth' });
    const done = () => { snapping = false; then?.(); };
    if (reduced.matches) return done();
    let last = -1, still = 0;
    const watch = () => { // 等滚动停下：scrollend 不是所有浏览器都有。
      if (window.scrollY === last && ++still > 3) return done();
      if (window.scrollY !== last) still = 0;
      last = window.scrollY; requestAnimationFrame(watch);
    };
    requestAnimationFrame(watch);
  }
  const enter = at => { show(at); scrollToY(window.scrollY + top()); };
  function move(direction) {
    if (direction > 0 && index === steps.length - 1) return scrollToY(window.scrollY + tour.getBoundingClientRect().bottom);
    if (direction < 0 && index === 0) return scrollToY(0);
    show(index + direction);
    // 换步会改变说明区的内容；保持第二屏贴住视口顶部。
    if (!pinned()) window.scrollTo({ top: window.scrollY + top(), behavior: 'auto' });
  }

  // 一次手势只切一步：切完后，要等滚轮停 160ms 以上（触控板的惯性也算同一次）才接受下一步。
  let locked = false, lastWheel = 0, stepAt = 0, sum = 0;
  function scrollable(target, delta) {
    for (let el = target; el && el !== wb; el = el.parentElement) {
      const style = getComputedStyle(el);
      if (!/(auto|scroll)/.test(style.overflowY) || el.scrollHeight <= el.clientHeight + 1) continue;
      if (delta > 0 ? el.scrollTop + el.clientHeight < el.scrollHeight - 1 : el.scrollTop > 0) return true;
    }
    return false;
  }
  window.addEventListener('wheel', event => {
    const now = performance.now();
    const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? innerHeight : 1);
    const gap = now - lastWheel;
    lastWheel = now;
    if (snapping) { event.preventDefault(); return; }
    const t = top(), h = innerHeight;
    if (near()) {
      repin();
      if (wb.contains(event.target) && scrollable(event.target, delta)) { locked = true; return; }
      event.preventDefault();
      if (locked && (gap < 160 || now - stepAt < 350)) return;
      locked = false;
      sum = gap > 160 ? delta : sum + delta;
      if (Math.abs(sum) < 24) return;
      sum = 0; locked = true; stepAt = now;
      move(Math.sign(delta));
    } else if (delta > 0 && t > 0 && t <= h + 1) { // 首屏往下：进入第一步（或回到上次看到的那步）。
      event.preventDefault(); locked = true; stepAt = now; enter(index);
    } else if (delta < 0 && t < 0 && t > -h) { // 下载说明往上：回到最后一步（near 已排除只差几像素的情况）。
      event.preventDefault(); locked = true; stepAt = now; enter(steps.length - 1);
    }
  }, { passive: false });

  window.addEventListener('keydown', event => {
    if (!near() || event.altKey || event.metaKey || event.ctrlKey) return;
    // 焦点在演示窗口里时，按键归演示自己用。
    if (wb.contains(event.target) || event.target.closest('input, textarea, select, [contenteditable]') || (event.key === ' ' && event.target.closest('button'))) return;
    const direction = { ArrowDown: 1, PageDown: 1, ' ': 1, ArrowUp: -1, PageUp: -1 }[event.key];
    if (!direction) return;
    event.preventDefault(); repin(); move(event.shiftKey && event.key === ' ' ? -1 : direction);
  });

  // 触摸：第二屏贴顶时，一次滑动换一步；还没贴顶时，手指离开且第二屏露出大半，就贴到第二屏。
  let touchY = null, touchPinned = false;
  window.addEventListener('touchstart', event => { touchY = event.touches[0].clientY; touchPinned = near(); }, { passive: true });
  tour.addEventListener('touchmove', event => { if (touchPinned && !scrollable(event.target, touchY - event.touches[0].clientY)) event.preventDefault(); }, { passive: false });
  window.addEventListener('touchend', event => {
    if (touchY === null || snapping) return;
    const dy = touchY - event.changedTouches[0].clientY; touchY = null;
    if (touchPinned) {
      repin();
      if (tour.contains(event.target) && Math.abs(dy) > 48 && !scrollable(event.target, dy)) move(Math.sign(dy));
    } else settle(() => { if (Math.abs(top()) < innerHeight * .6) enter(index); });
  });
  // 手指离开后还有惯性滚动；等页面停下再决定贴不贴。
  function settle(then) {
    let last = NaN, still = 0;
    const watch = () => {
      if (window.scrollY === last && ++still > 5) return then();
      if (window.scrollY !== last) still = 0;
      last = window.scrollY; requestAnimationFrame(watch);
    };
    requestAnimationFrame(watch);
  }

  dots.addEventListener('click', event => {
    const dot = event.target.closest('[data-dot]');
    if (dot) { show(Number(dot.dataset.dot)); if (!pinned()) scrollToY(window.scrollY + top()); }
  });
  tour.querySelector('[data-tour-reset]').addEventListener('click', () => { demo.go('reset'); show(index); });
  // 导航里的“演示”与首屏的“看演示”：对齐到第二屏，从当前一步看起。
  document.querySelectorAll('a[href="#demo"]').forEach(link => link.addEventListener('click', event => { event.preventDefault(); enter(index); }));

  show(0);
  fit();
})();
