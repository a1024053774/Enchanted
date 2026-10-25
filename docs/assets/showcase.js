// 分功能展示：每个展示挂一份演示窗口，各自分步；页面照常滚动，不劫持滚轮。
// 展示之间用一条紫色轨道线连起来：随滚动画出，线头不超过视口一半；经过每个展示时点亮它的四角星，沿途的小珠子依次出现。
// 轨道和四角星取自 Enchanted 标志里的环绕轨道与星。减弱动效时线一次画全，不做过渡。
(() => {
  'use strict';
  const Demo = window.EnchantedDemo;
  if (!Demo) return;
  const calm = matchMedia('(prefers-reduced-motion: reduce)');
  const shows = [...document.querySelectorAll('.show')];
  const firstHint = document.querySelector('[data-show-first]');
  let seenKey = 'enchanted-showcase-seen', seen = false;
  try { seen = localStorage.getItem(seenKey) === '1'; } catch (error) { /* 读不到时每次都提示 */ }

  // 收起提示只让它不可见、不收起它的位置：页面在你按下鼠标的那一刻不能移动，否则松开时点到的是别的东西。
  function dismissHint() {
    if (!firstHint || firstHint.hidden || firstHint.dataset.dismissed) return;
    firstHint.dataset.dismissed = '';
    firstHint.closest('.show')?.classList.remove('is-first');
    try { localStorage.setItem(seenKey, '1'); } catch (error) { /* 只在本次浏览中生效 */ }
  }

  function setup(show, at) {
    const steps = [...show.querySelectorAll('[data-show-steps] > li')];
    const wb = show.querySelector('.wb');
    const stage = show.querySelector('[data-show-stage]'), frame = show.querySelector('[data-show-frame]');
    const nav = show.querySelector('[data-show-nav]');
    const prev = show.querySelector('[data-show-prev]'), next = show.querySelector('[data-show-next]');
    const nextLabel = next?.firstChild;
    const following = shows[at + 1];
    let demo = null, index = 0;
    show.classList.add('is-live');
    if (nav) nav.hidden = false;

    // 窗口按桌面尺寸 1040×760 还原，按舞台宽度整体缩放。
    function fit() {
      if (!demo) return;
      const scale = Math.min(1, stage.clientWidth / wb.offsetWidth);
      frame.style.height = wb.offsetHeight * scale + 'px';
      wb.style.transform = `scale(${scale})`;
    }

    function go(to) {
      index = Math.max(0, Math.min(steps.length - 1, to));
      steps.forEach((step, i) => step.classList.toggle('is-current', i === index));
      const count = show.querySelector('[data-show-index]');
      if (count) count.textContent = index + 1;
      if (prev) prev.disabled = index === 0;
      if (next) {
        const last = index === steps.length - 1;
        next.disabled = last && !following;
        nextLabel.textContent = last && following ? '下一个功能' : '下一步';
      }
      demo?.go(steps[index].dataset.scene);
    }

    function mount() {
      if (demo) return;
      wb.innerHTML = '';
      demo = Demo.mount(wb);
      new ResizeObserver(fit).observe(stage);
      fit();
      go(index);
    }

    prev?.addEventListener('click', () => { dismissHint(); go(index - 1); });
    next?.addEventListener('click', () => {
      dismissHint();
      if (index === steps.length - 1 && following) {
        following.scrollIntoView({ behavior: calm.matches ? 'auto' : 'smooth', block: 'start' });
        following.querySelector('[data-show-next], [data-show-stage] button')?.focus({ preventScroll: true });
      } else go(index + 1);
    });
    // 焦点在说明区时，左右方向键换步；演示窗口里的方向键留给窗口自己（菜单、列表）。
    show.querySelector('.show-guide').addEventListener('keydown', event => {
      if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
      event.preventDefault();
      dismissHint();
      go(index + (event.key === 'ArrowRight' ? 1 : -1));
    });
    if (show.contains(firstHint)) wb.addEventListener('pointerdown', dismissHint);
    return { mount, show };
  }

  const items = shows.map(setup);
  // 首屏的展示立刻挂上；其余的快滚到时再挂，避免一次渲染六个窗口。
  items[0].mount();
  if (firstHint && !seen) { firstHint.hidden = false; firstHint.closest('.show')?.classList.add('is-first'); }
  const lazy = new IntersectionObserver(entries => {
    for (const entry of entries) if (entry.isIntersecting) {
      items.find(item => item.show === entry.target)?.mount();
      lazy.unobserve(entry.target);
    }
  }, { rootMargin: '600px 0px' });
  items.slice(1).forEach(item => lazy.observe(item.show));

  // ---------- 轨道线 ----------
  const svg = document.querySelector('[data-thread]');
  const main = document.querySelector('main');
  if (!svg || !main) return;
  const line = svg.querySelector('[data-thread-line]'), glow = svg.querySelector('[data-thread-glow]');
  const beadGroup = svg.querySelector('[data-thread-beads]');
  const stars = [...document.querySelectorAll('[data-station-star]')];
  const NS = 'http://www.w3.org/2000/svg';
  let total = 0, table = [], marks = [];

  // 每颗星是一站：线从一颗星竖直往下，走到两段展示之间的空白处再弯到下一颗星的竖线上，
  // 横向的弯只出现在展示之间，不压在说明文字上。
  function layout() {
    const box = main.getBoundingClientRect();
    svg.setAttribute('width', box.width); svg.setAttribute('height', main.scrollHeight);
    svg.setAttribute('viewBox', `0 0 ${box.width} ${main.scrollHeight}`);
    const points = stars.map(star => {
      const r = star.getBoundingClientRect(), owner = star.closest('.show').getBoundingClientRect();
      return { x: r.left + r.width / 2 - box.left, y: r.top + r.height / 2 - box.top, end: owner.bottom - box.top };
    });
    if (points.length < 2) return;
    let d = `M${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1], b = points[i];
      const gapTop = Math.min(a.end, b.y - 40), gapBottom = b.y - 24;
      const bend = Math.max(24, (gapBottom - gapTop) / 2);
      d += ` L${a.x} ${gapTop} C${a.x} ${gapTop + bend} ${b.x} ${gapBottom - bend} ${b.x} ${gapBottom} L${b.x} ${b.y}`;
    }
    const last = points[points.length - 1];
    d += ` L${last.x} ${last.end}`;
    line.setAttribute('d', d); glow.setAttribute('d', d);
    total = line.getTotalLength();
    [line, glow].forEach(path => { path.style.strokeDasharray = `${total} ${total}`; });
    // 线上每一点按长度采样一次，滚动时按纵坐标查长度。线从上往下单调，二分即可。
    table = [];
    for (let at = 0; at <= total; at += 6) table.push([at, line.getPointAtLength(at).y]);
    table.push([total, line.getPointAtLength(total).y]);
    const lengthAt = y => {
      let lo = 0, hi = table.length - 1;
      // 取纵坐标不超过 y 的最后一个采样点，线头不会越过半屏。
      while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (table[mid][1] <= y) lo = mid; else hi = mid - 1; }
      return table[lo][0];
    };
    beadGroup.replaceChildren();
    marks = points.map((p, i) => ({ at: lengthAt(p.y) - 1, el: stars[i] }));
    for (let at = 90; at < total - 40; at += 150) {
      if (marks.some(mark => Math.abs(mark.at - at) < 60)) continue;
      const p = line.getPointAtLength(at), bead = document.createElementNS(NS, 'circle');
      bead.setAttribute('cx', p.x); bead.setAttribute('cy', p.y); bead.setAttribute('r', 3.2);
      bead.setAttribute('class', 'thread-bead');
      bead.style.transformOrigin = `${p.x}px ${p.y}px`;
      beadGroup.append(bead);
      marks.push({ at, el: bead });
    }
    layout.lengthAt = lengthAt;
    draw();
  }

  function draw() {
    if (!total) return;
    const head = calm.matches ? total
      : Math.max(0, layout.lengthAt(scrollY + innerHeight * .5 - (main.getBoundingClientRect().top + scrollY)));
    const offset = total - head;
    line.style.strokeDashoffset = offset; glow.style.strokeDashoffset = offset;
    for (const mark of marks) mark.el.classList.toggle('is-lit', mark.at <= head);
  }

  let queued = false;
  addEventListener('scroll', () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; draw(); });
  }, { passive: true });
  calm.addEventListener('change', draw);
  new ResizeObserver(() => requestAnimationFrame(layout)).observe(main);
  svg.classList.add('is-live');
  layout();
})();
