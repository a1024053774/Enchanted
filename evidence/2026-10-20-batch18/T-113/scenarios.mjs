// T-113 演示交互的逐项检查。预期来自 T-113 票列出的交互和真实工作台的行为
// （workbench/app/renderer.tsx、FlowPage.tsx、QuestionsPanel.tsx、AppNotifications.tsx、workbench/src/sidebar.ts），
// 不取自本页实现的输出。
const q = JSON.stringify;
const text = (page, selector) => page.eval(`document.querySelector(${q(selector)})?.textContent.replace(/\\s+/g, ' ').trim() ?? null`);
const attr = (page, selector, name) => page.eval(`document.querySelector(${q(selector)})?.getAttribute(${q(name)}) ?? null`);
const count = (page, selector) => page.eval(`document.querySelectorAll(${q(selector)}).length`);
const visibleCount = (page, selector) => page.eval(`[...document.querySelectorAll(${q(selector)})].filter(el => el.getClientRects().length).length`);
const focused = page => page.eval(`(() => { const el = document.activeElement; return el ? (el.getAttribute('data-fk') || el.textContent.trim()) : null; })()`);
const rect = (page, selector) => page.eval(`(() => { const r = document.querySelector(${q(selector)})?.getBoundingClientRect(); return r && { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) }; })()`);
const paneOf = launch => `.pane[data-launch-id="${launch}"]`;
const press = (page, viewport, selector) => viewport === 'phone' ? page.tap(selector) : page.click(selector);
const noPageScrollX = page => page.eval('document.documentElement.scrollWidth <= window.innerWidth');

export default [
  { name: '01 侧栏切换项目', async run({ page, url, viewport, check }) {
    await page.load(url);
    check('演示已渲染', await attr(page, '#wb-demo', 'data-ready') === 'true');
    check('初始选中 inkwell', await attr(page, '[data-project-id="inkwell"]', 'aria-current') === 'page');
    await press(page, viewport, '[data-project-id="tidepool"]');
    check('tidepool 变为当前项目', await attr(page, '[data-project-id="tidepool"]', 'aria-current') === 'page');
    check('inkwell 不再是当前项目', await attr(page, '[data-project-id="inkwell"]', 'aria-current') === null);
    check('标题切到 tidepool 的首个任务', await text(page, '.wb h1') === '离线队列重试改为指数退避');
    check('agent 树换成 tidepool 的 11 个会话', await count(page, '[data-agent-launch]') === 11);
    check('未恢复的执行主控在窗格里给出原因', (await text(page, paneOf('launch-93fe') + ' [role="alert"]'))?.startsWith('未恢复：'));
    await press(page, viewport, '[data-project-id="ledger-cli"]');
    check('无会话项目显示空状态', (await text(page, '.agent-list')).includes('这个项目还没有 agent 启动记录。'));
    check('无会话项目状态为未知', await attr(page, '[data-project-id="ledger-cli"]', 'data-project-state') === 'unknown');
    check('无会话项目分支行显示未设置上游', (await text(page, '[data-project-id="ledger-cli"] .project-git')).includes('未设置上游'));
    await page.shot(`${viewport}-01-project-switch`);
  } },

  { name: '02 层级树、七种状态、点击聚焦、折叠汇总', async run({ page, url, viewport, check }) {
    await page.load(url);
    const states = new Set(await page.eval(`[...document.querySelectorAll('[data-agent-state]')].map(el => el.dataset.agentState)`));
    check('构思主控在第 0 层', await attr(page, '[data-agent-launch="launch-41c7"]', 'data-agent-level') === '0');
    check('执行主控在第 1 层', await attr(page, '[data-agent-launch="launch-8e02"]', 'data-agent-level') === '1');
    check('worker 在第 2 层、挂在任务 T-12 下', await attr(page, '[data-agent-launch="launch-a3f9"]', 'data-agent-level') === '2'
      && await page.eval(`document.querySelector('[data-agent-launch="launch-a3f9"]').closest('.agent-task-group').querySelector('.agent-task-label').textContent`) === '任务 T-12');
    check('没有父记录的会话在“未归属”下', await page.eval(`!!document.querySelector('.unassigned-agents [data-agent-launch="launch-0b9d"]')`));
    await press(page, viewport, '[data-project-id="tidepool"]');
    (await page.eval(`[...document.querySelectorAll('[data-agent-state]')].map(el => el.dataset.agentState)`)).forEach(s => states.add(s));
    const expected = ['running', 'waiting_user_answer', 'waiting_controller_answer', 'idle', 'ended', 'unrestored', 'unknown'];
    check('两个项目合起来覆盖七种状态', expected.every(s => states.has(s)), [...states].join(','));
    check('状态文字为中文', (await text(page, '[data-agent-launch="launch-f40c"] .agent-state')) === '未知');
    await press(page, viewport, '[data-project-id="inkwell"]');
    await press(page, viewport, '[data-agent-launch="launch-e7b4"]');
    check('点击 agent 后切到它的任务 T-14', await text(page, '.wb .eyebrow') === 'inkwell / T-14');
    check('该 agent 行高亮', await attr(page, '[data-agent-launch="launch-e7b4"]', 'aria-current') === 'true');
    check('对应窗格获得焦点框', await page.eval(`document.querySelector(${q(paneOf('launch-e7b4'))}).classList.contains('pane-focused')`));
    await press(page, viewport, '[data-agent-launch="launch-c611"]');
    check('没有打开窗格的监视器被打开并聚焦', await page.eval(`document.querySelector(${q(paneOf('launch-c611'))})?.classList.contains('pane-focused') ?? false`));
    await press(page, viewport, '[data-agent-toggle="launch-8e02"]');
    check('折叠后子会话隐藏', await attr(page, '#wb-children-launch-8e02', 'hidden') !== null);
    check('折叠后显示子会话汇总', (await text(page, '[data-agent-summary="launch-8e02"]')) === '◑子会话 5 · 运行中 2 · 等待主控回答 1 · 空闲 2');
    check('汇总状态取最需要处理的（等待主控回答）', await attr(page, '[data-agent-launch="launch-8e02"]', 'data-descendant-state') === 'waiting_controller_answer');
    check('折叠按钮报告 aria-expanded=false', await attr(page, '[data-agent-toggle="launch-8e02"]', 'aria-expanded') === 'false');
    await page.shot(`${viewport}-02-tree-collapsed`);
    await press(page, viewport, '[data-agent-toggle="launch-8e02"]');
    check('再次点击展开', await attr(page, '#wb-children-launch-8e02', 'hidden') === null);
    await press(page, viewport, '[data-task-option="T-11"]');
    check('任务条切换到 T-11', await text(page, '.wb h1') === '导入时保留原始时间戳' && await text(page, '.gate strong') === '已交付');
    check('T-11 显示两个窗格', await count(page, '.pane-slot:not([hidden])') === 2);
  } },

  { name: '03 提问面板作答、状态回落、应用内通知', async run({ page, url, viewport, check, sleep }) {
    await page.load(url);
    const notice = await page.eval(`[...(document.querySelector('[data-notice-launch="launch-41c7"]')?.children ?? [])].map(el => el.textContent.trim()).join('|')`);
    check('通知可见：等待用户回答', notice === '等待用户回答|inkwell · 构思主控|T-12 · 查看问题 →', notice);
    check('Dock 角标为 1', (await text(page, '[data-dock] b')) === '1');
    check('项目行标为等待用户回答', await attr(page, '[data-project-id="inkwell"]', 'data-project-state') === 'waiting_user_answer');
    await press(page, viewport, '[data-project-id="tidepool"]');
    await press(page, viewport, '[data-notice-launch="launch-41c7"]');
    check('点通知后回到 inkwell / T-12', await text(page, '.wb .eyebrow') === 'inkwell / T-12');
    check('点通知后聚焦构思主控的窗格', await page.eval(`document.querySelector(${q(paneOf('launch-41c7'))}).classList.contains('pane-focused')`));
    const form = '[data-question-id="q-1"]';
    check('提问面板显示“等待用户回答”', (await text(page, form + ' .question-heading strong')) === '等待用户回答');
    check('未选时发送按钮禁用', await page.eval(`document.querySelector('${form} > button').disabled`));
    await press(page, viewport, form + ' [data-option="不包含"]');
    check('选项标为已选', await attr(page, form + ' [data-option="不包含"]', 'aria-pressed') === 'true');
    check('答复框填入选项', await page.eval(`document.querySelector('${form} input').value`) === '不包含');
    check('选中后发送按钮可用', await page.eval(`!document.querySelector('${form} > button').disabled`));
    await page.shot(`${viewport}-03-question-selected`);
    await press(page, viewport, form + ' > button');
    check('发送后显示“已送入窗格”', (await text(page, form + ' [role="status"]')) === '答复已送入窗格，等待原生确认。');
    await sleep(1300);
    check('提问面板消失', await count(page, form) === 0);
    check('构思主控回落为运行中', await attr(page, '[data-agent-launch="launch-41c7"]', 'data-agent-state') === 'running');
    check('通知消失', await count(page, '[data-notice-launch]') === 0);
    check('Dock 角标清空', (await text(page, '[data-dock]')) === '');
    check('项目行改按剩余状态汇总（等待主控回答）', await attr(page, '[data-project-id="inkwell"]', 'data-project-state') === 'waiting_controller_answer');
    check('答复写回终端', (await text(page, paneOf('launch-41c7') + ' .terminal-lines')).includes('› 不包含'));
    await page.shot(`${viewport}-03-question-answered`);
    await press(page, viewport, '[data-demo-go="reset"]');
    check('重置后通知回来', await count(page, '[data-notice-launch="launch-41c7"]') === 1);
    await press(page, viewport, '.sidebar-settings summary');
    await press(page, viewport, '[data-setting="notifications"]');
    check('关掉应用内通知后通知消失', await count(page, '[data-notice-launch]') === 0);
    check('关掉通知不影响 Dock 角标', (await text(page, '[data-dock] b')) === '1');
    await press(page, viewport, '[data-setting="dockBadges"]');
    check('关掉 Dock 角标后角标消失', (await text(page, '[data-dock]')) === '');
    check('图例列出七种状态', await count(page, '.status-legend > span') === 7);
  } },

  { name: '03b 非默认选项、自由答复、通知开关往返', async run({ page, url, viewport, check, sleep }) {
    // 预期：终端宣称的决定必须与用户所选一致（真实 QuestionsPanel 把所选答案原样送入窗格）；
    // 自由答复只确认收到原文；通知按 notificationCenter.ts：关闭时清空、保留已提醒记录，重新开启不重放，Dock 待答数与开关分离。
    const send = async (question, launch, option) => {
      await page.load(url);
      await press(page, viewport, `[data-agent-launch="${launch}"]`);
      await press(page, viewport, `[data-question-id="${question}"] [data-option="${option}"]`);
      await press(page, viewport, `[data-question-id="${question}"] > button`);
      await sleep(1300);
      return text(page, paneOf(launch) + ' .terminal-lines');
    };
    const included = await send('q-1', 'launch-41c7', '包含');
    check('选“包含”后写回所选答案', included.includes('› 包含'));
    check('选“包含”后终端说的是包含', included.includes('默认包含已归档条目') && !included.includes('默认不包含已归档条目'), included.slice(-120));
    const kept = await send('q-2', 'launch-e7b4', '保留一个版本');
    check('选“保留一个版本”后终端说的是保留', kept.includes('保留 0.8 迁移代码') && !kept.includes('删除 0.8 迁移代码'), kept.slice(-120));
    await page.load(url);
    await press(page, viewport, '[data-agent-launch="launch-e7b4"]');
    await press(page, viewport, '[data-question-id="q-2"] input');
    await page.type('先问维护者再定');
    await press(page, viewport, '[data-question-id="q-2"] > button');
    await sleep(1300);
    const free = await text(page, paneOf('launch-e7b4') + ' .terminal-lines');
    check('自由答复原文写回终端', free.includes('› 先问维护者再定'));
    check('自由答复只确认收到，不套用预设决定', free.includes('收到答复，按上面这行原文继续') && !free.includes('删除 0.8 迁移代码') && !free.includes('保留 0.8 迁移代码'), free.slice(-120));
    await page.load(url);
    await press(page, viewport, '.sidebar-settings summary');
    await press(page, viewport, '[data-setting="notifications"]');
    check('关闭通知后通知清空', await count(page, '[data-notice-launch]') === 0);
    await press(page, viewport, '[data-setting="notifications"]');
    check('重新开启后不重放同一问题', await count(page, '[data-notice-launch]') === 0);
    check('Dock 待答数不受通知开关影响', (await text(page, '[data-dock] b')) === '1');
    check('侧栏仍标为等待用户回答', await attr(page, '[data-agent-launch="launch-41c7"]', 'data-agent-state') === 'waiting_user_answer');
  } },

  { name: '04 窗格菜单：分屏、放大、重命名、转发右键、关闭', async run({ page, url, viewport, check }) {
    await page.load(url);
    const worker = paneOf('launch-a3f9');
    const trigger = worker + ' .pane-menu-trigger';
    if (viewport === 'desktop') await page.click(worker + ' .pane-header strong', 'right');
    else await press(page, viewport, trigger);
    const items = await page.eval(`[...document.querySelectorAll('.pane-menu button')].map(b => b.textContent.trim())`);
    check('菜单有六项且顺序同真实应用', items.join('|') === '重命名窗格|向右分屏|向下分屏|放大|把右键发给窗格|关闭窗格', items.join('|'));
    check('打开菜单时焦点在第一项', await focused(page) === 'mi:rename');
    await page.key('ArrowDown', 'ArrowDown', 40);
    check('↓ 移到“向右分屏”', await focused(page) === 'mi:right');
    await page.key('End', 'End', 35);
    check('End 移到“关闭窗格”', await focused(page) === 'mi:close');
    await page.key('Escape', 'Escape', 27);
    check('Esc 关闭菜单', await count(page, '.pane-menu') === 0);
    check('Esc 后焦点回到 ⋯', await focused(page) === await attr(page, trigger, 'data-fk'));
    await page.shot(`${viewport}-04-before-split`);

    const before = await rect(page, worker);
    await press(page, viewport, trigger); await press(page, viewport, '[data-fk="mi:right"]');
    check('向右分屏后多一个窗格', await count(page, '.pane') === 4);
    const shell = '.pane[data-launch-id=""]';
    const left = await rect(page, worker), right = await rect(page, shell);
    check('新窗格是普通终端', (await text(page, shell + ' .pane-header strong')) === '普通终端');
    check('原窗格宽度减半、新窗格在右侧同一行', Math.abs(left.w * 2 - before.w) <= 4 && right.x > left.x && Math.abs(right.y - left.y) <= 2, JSON.stringify({ before, left, right }));
    await press(page, viewport, shell + ' .pane-menu-trigger'); await press(page, viewport, '[data-fk="mi:down"]');
    const shells = await page.eval(`[...document.querySelectorAll('.pane[data-launch-id=""]')].map(el => { const r = el.getBoundingClientRect(); return { x: Math.round(r.left), y: Math.round(r.top) }; })`);
    check('向下分屏后新窗格在下方', shells.length === 2 && shells[1].y > shells[0].y && Math.abs(shells[1].x - shells[0].x) <= 2, JSON.stringify(shells));
    await page.shot(`${viewport}-04-split`);

    await press(page, viewport, trigger); await press(page, viewport, '[data-fk="mi:zoom"]');
    check('放大后只显示这一格', await visibleCount(page, '.pane') === 1 && (await rect(page, worker)).w > before.w - 4);
    await press(page, viewport, trigger);
    check('放大后菜单项变为“还原”', (await text(page, '[data-fk="mi:zoom"]')) === '还原');
    await press(page, viewport, '[data-fk="mi:zoom"]');
    check('还原后各格重新可见', await visibleCount(page, '.pane') === 5);

    await press(page, viewport, trigger); await press(page, viewport, '[data-fk="mi:rename"]');
    check('重命名输入框获得焦点并带当前名字', await page.eval(`document.activeElement?.dataset.renameInput !== undefined && document.activeElement.value === '受管 worker'`));
    await page.type('标签筛选实现');
    await page.key('Enter', 'Enter', 13);
    check('标题栏显示新名字、保留角色', (await text(page, worker + ' .pane-header strong')) === '标签筛选实现' && (await text(page, worker + ' .pane-header > span'))?.startsWith('受管 worker'));

    if (viewport === 'desktop') {
      await press(page, viewport, trigger); await press(page, viewport, '[data-fk="mi:forward"]');
      await press(page, viewport, trigger);
      check('转发右键勾选后菜单显示 ✓', await attr(page, '[data-fk="mi:forward"]', 'aria-checked') === 'true' && (await text(page, '[data-fk="mi:forward"]')).startsWith('✓'));
      await page.key('Escape', 'Escape', 27);
      await page.click(worker + ' .terminal-scroll', 'right');
      check('在终端区右键不弹菜单', await count(page, '.pane-menu') === 0);
      check('右键转给窗格里的程序', (await text(page, worker + ' .terminal-lines')).endsWith('（右键已作为鼠标事件发给窗格里的程序）'));
      await page.click(worker + ' .pane-header strong', 'right');
      check('在标题栏右键仍弹菜单', await count(page, '.pane-menu') === 1);
      await page.key('Escape', 'Escape', 27);
    }
    for (let i = 0; i < 2; i++) { await press(page, viewport, '.pane[data-launch-id=""] .pane-menu-trigger'); await press(page, viewport, '[data-fk="mi:close"]'); }
    check('关闭两个普通终端后回到三格', await count(page, '.pane') === 3);
    const back = await rect(page, worker);
    check('关闭后 worker 恢复整行宽度', Math.abs(back.w - before.w) <= 2, JSON.stringify({ back, before }));
  } },

  { name: '05 流程页：泳道、阶段、胶囊、折回线、还有 N 个', async run({ page, url, viewport, check }) {
    await page.load(url);
    await press(page, viewport, '[data-flow-tab]');
    check('流程标签为当前页', await attr(page, '[data-flow-tab]', 'aria-current') === 'page');
    check('终端页隐藏', await attr(page, '.terminal-page', 'hidden') !== null);
    check('每张票一条泳道（7 张）', await count(page, '.flow-lane') === 7);
    const lane = '[data-flow-task="T-11"]';
    check('T-11 处于独立审查阶段', await attr(page, lane, 'data-flow-stage') === 'review' && await attr(page, lane + ' [data-flow-column="review"]', 'aria-current') === 'step');
    check('T-11 标题行写打回 2 次', (await text(page, lane + ' .flow-lane-heading > span')).endsWith('打回 2 次'));
    check('折回线分来源计数', await attr(page, lane + ' [data-flow-return="checks"]', 'data-return-count') === '1' && await attr(page, lane + ' [data-flow-return="review"]', 'data-return-count') === '1');
    check('审查员胶囊在独立审查列、worker 在实现列', await page.eval(`!!document.querySelector('${lane} [data-flow-column="review"] [data-flow-agent="launch-5d20"]') && !!document.querySelector('${lane} [data-flow-column="implementation"] [data-flow-agent="launch-2a6e"]')`));
    check('监视器在泳道上方“贯穿监视”', await page.eval(`!!document.querySelector('[data-flow-task="T-12"] .flow-monitors [data-flow-agent="launch-c611"]')`));
    check('阶段无法确认时写“阶段未知”', (await text(page, '[data-flow-task="T-3"] .flow-lane-heading > span')).includes('阶段未知 · 核对门禁记录'));
    const integrated = '[data-flow-toggle="T-09"]';
    check('已集成的票默认折叠', await attr(page, integrated, 'aria-expanded') === 'false' && await count(page, '[data-flow-task="T-09"] .flow-stages') === 0);
    await press(page, viewport, integrated);
    check('点开已集成的票，五个阶段都已完成', await count(page, '[data-flow-task="T-09"] .flow-stage.complete') === 5);
    const group = '[data-flow-task="T-5"] [data-flow-column="implementation"]';
    check('超过四个时先显示四个', await count(page, group + ' .flow-agent') === 4 && (await text(page, '[data-flow-more="T-5-implementation"]')) === '还有 2 个 ↗');
    await press(page, viewport, '[data-flow-more="T-5-implementation"]');
    check('展开后显示全部 6 个并可收起', await count(page, group + ' .flow-agent') === 6 && (await text(page, '[data-flow-more="T-5-implementation"]')) === '收起');
    check('未归属会话单列', await page.eval(`!!document.querySelector('.flow-unassigned [data-flow-agent="launch-7a31"]')`));
    check('泳道区可横向滚动', await page.eval(`(() => { const el = document.querySelector('.flow-scroll'); return el.scrollWidth > el.clientWidth; })()`));
    await page.shot(`${viewport}-05-flow`);
    await press(page, viewport, '[data-fk="page:terminal"]');
    check('切回终端页', await attr(page, '.terminal-page', 'hidden') === null);
  } },

  { name: '06 终端预设输出、独立终端、新建终端', async run({ page, url, viewport, check }) {
    await page.load(url);
    check('worker 终端有预设的红态输出', (await text(page, paneOf('launch-a3f9') + ' .terminal-lines')).includes('3 failed（红态，符合预期）'));
    await press(page, viewport, '[data-task-option="T-11"]');
    check('审查员窗格标为只读', (await text(page, paneOf('launch-5d20') + ' .readonly')) === '只读' && (await text(page, paneOf('launch-5d20') + ' .pane-footer span'))?.startsWith('独立审查 · 只读'));
    check('worker 窗格提示输入会记为人工介入', (await text(page, paneOf('launch-2a6e') + ' .pane-footer span')) === '在此窗格输入会记录为人工介入');
    await press(page, viewport, '[data-fk="free"]');
    check('独立终端页', await text(page, '.wb h1') === '独立终端' && await attr(page, '[data-fk="free"]', 'aria-current') === 'page');
    check('普通终端有预设命令输出', (await text(page, '.pane .terminal-lines')).startsWith('~ % git status -sb'));
    await press(page, viewport, '[data-fk="new-terminal"]');
    check('新建终端后多一个窗格', await count(page, '.pane') === 2);
    await page.shot(`${viewport}-06-free-terminals`);
  } },

  { name: '07 键盘可达', viewports: ['desktop'], async run({ page, url, check }) {
    await page.load(url);
    await page.eval(`document.querySelector('[data-project-id="tidepool"]').focus()`);
    await page.key('Enter', 'Enter', 13);
    check('Enter 选中项目', await attr(page, '[data-project-id="tidepool"]', 'aria-current') === 'page');
    check('重绘后焦点留在该项目', await focused(page) === 'project:tidepool');
    await page.key('Tab', 'Tab', 9);
    check('Tab 移到下一个项目', await focused(page) === 'project:ledger-cli');
    await page.eval(`document.querySelector('[data-agent-toggle="launch-62aa"]').focus()`);
    await page.key(' ', 'Space', 32);
    check('空格折叠层级', await attr(page, '[data-agent-toggle="launch-62aa"]', 'aria-expanded') === 'false');
    await page.eval(`document.querySelector('[data-demo-go="question"]').focus()`);
    await page.key('Enter', 'Enter', 13);
    check('引导按钮把焦点带到提问选项', (await focused(page))?.startsWith('option:q-1'));
    check('焦点有可见轮廓', await page.eval(`getComputedStyle(document.activeElement).outlineStyle !== 'none'`));
  } },

  { name: '08 版式：无横向页面滚动、窄屏画布、主题', async run({ page, url, viewport, check, sleep }) {
    await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }] });
    await page.load(url);
    check('页面无横向滚动', await noPageScrollX(page), String(await page.eval('document.documentElement.scrollWidth')));
    check('跟随系统深色', await page.eval(`getComputedStyle(document.body).backgroundColor`) === 'rgb(17, 17, 17)');
    if (viewport === 'phone') {
      check('演示画布在窄屏可左右滚动', await page.eval(`(() => { const el = document.querySelector('.demo-canvas'); return el.scrollWidth > el.clientWidth; })()`));
      check('窄屏显示左右滑动提示', await visibleCount(page, '.demo-hint') === 1);
    }
    await press(page, viewport, '[data-theme-toggle]');
    check('切到浅色', await attr(page, 'html', 'data-theme') === 'light' && await page.eval(`getComputedStyle(document.body).backgroundColor`) === 'rgb(246, 246, 244)');
    check('浅色下演示窗口仍是工作台深色', await page.eval(`getComputedStyle(document.querySelector('#wb-demo')).backgroundColor`) === 'rgb(17, 17, 17)');
    await page.shot(`${viewport}-08-light`);
    await press(page, viewport, '[data-theme-toggle]');
    check('切到深色', await attr(page, 'html', 'data-theme') === 'dark');
    await page.load(url);
    check('主题选择在刷新后保留', await attr(page, 'html', 'data-theme') === 'dark');
    await press(page, viewport, '[data-theme-toggle]');
    check('回到跟随系统', await attr(page, 'html', 'data-theme') === null && (await text(page, '[data-theme-toggle]')) === '主题：跟随系统');
    await page.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }] });
    await sleep(100);
    check('跟随系统浅色', await page.eval(`getComputedStyle(document.body).backgroundColor`) === 'rgb(246, 246, 244)');
    await press(page, viewport, '[data-flow-tab]');
    check('打开流程页后页面仍无横向滚动', await noPageScrollX(page));
    await page.shot(`${viewport}-08-page`);
    await page.send('Emulation.setEmulatedMedia', { features: [] });
  } },

  { name: '10 会话模型设置（T-112）', async run({ page, url, viewport, check }) {
    // 预期取自 T-112 Resolution：Codex 角色出厂默认 gpt-6.1-sol high、不传 Fast；两个主控 claude-haiku-5-5 low；保存后下次启动生效。
    await page.load(url);
    await press(page, viewport, '.sidebar-settings summary');
    const value = field => page.eval(`document.querySelector('[data-exec-field="${field}"]').${field === 'fast' ? 'checked' : 'value'}`);
    const pickRole = role => page.eval(`(() => { const s = document.querySelector('[data-exec-role]'); s.value = ${q(role)}; s.dispatchEvent(new Event('change', { bubbles: true })); })()`);
    check('设置里有“会话模型”区块', (await text(page, '.execution-settings strong')) === '会话模型');
    check('角色选项与真实应用一致', (await page.eval(`[...document.querySelectorAll('[data-exec-role] option')].map(o => o.textContent).join('|')`)) === 'Worker|审查员|监视器|构思主控|执行主控');
    check('Worker 出厂默认 gpt-6.1-sol / high / 不传 Fast', await value('model') === 'gpt-6.1-sol' && await value('effort') === 'high' && await value('fast') === false);
    await pickRole('ideation');
    check('构思主控出厂默认 claude-haiku-5-5 / low', await value('model') === 'claude-haiku-5-5' && await value('effort') === 'low');
    await page.eval(`document.querySelector('[data-exec-field="effort"]').select()`);
    await press(page, viewport, '[data-exec-field="effort"]');
    await page.eval(`document.querySelector('[data-exec-field="effort"]').select()`);
    await page.type('xhigh');
    await press(page, viewport, '[data-fk="exec:save"]');
    check('保存后提示下次启动生效', (await text(page, '.execution-settings [role="status"]')) === '已保存，下次启动生效');
    await pickRole('worker');
    check('切换角色后提示清空、Worker 不受影响', await count(page, '.execution-settings [role="status"]') === 0 && await value('effort') === 'high');
    await pickRole('ideation');
    check('构思主控保留新保存的 xhigh', await value('effort') === 'xhigh');
    await page.eval(`document.querySelector('[data-exec-field="effort"]').select()`);
    await page.type('max');
    await pickRole('worker'); await pickRole('ideation');
    check('没保存就切换角色，改动不生效', await value('effort') === 'xhigh');
    check('页面无横向滚动', await noPageScrollX(page));
    await page.shot(`${viewport}-10-execution-settings`);
  } },

  { name: '09 禁用 JavaScript 时内容可读', async run({ page, url, viewport, check }) {
    await page.send('Emulation.setScriptExecutionDisabled', { value: true });
    try {
      await page.load(url);
      const body = await page.eval('document.body.innerText');
      for (const needle of ['让 Claude Code 和 Codex', '为什么要门禁', '一张票怎么走完', '两层主控', '现在能用的', '已知限制', '路线图', '未做', '下载与安装', 'GPL-3.0', '可点击的演示需要 JavaScript。'])
        check(`可读：${needle}`, body.includes(needle));
      check('需要脚本的引导与按钮不显示', await visibleCount(page, '[data-tour], [data-demo-go="reset"], [data-theme-toggle]') === 0);
      check('页面无横向滚动', await noPageScrollX(page));
      await page.shot(`${viewport}-09-no-js`);
    } finally { await page.send('Emulation.setScriptExecutionDisabled', { value: false }); }
  } },
];
