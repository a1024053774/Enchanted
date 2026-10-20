// Enchanted 产品页的工作台演示：全部是预设的虚构数据，不连后台、不调模型。
// 结构与文案取自 workbench/app 的 renderer.tsx、FlowPage.tsx、QuestionsPanel.tsx、AppNotifications.tsx，
// 状态优先级取自 workbench/src/sidebar.ts，阶段取自 workbench/src/flowStages.ts。
(() => {
  'use strict';
  const root = document.getElementById('wb-demo');
  if (!root) return;

  const stateLabels = { running: '运行中', waiting_user_answer: '等待用户回答', waiting_controller_answer: '等待主控回答',
    idle: '空闲', ended: '已结束', unrestored: '未恢复', unknown: '未知' };
  const statusIcons = { running: '●', waiting_user_answer: '◐', waiting_controller_answer: '◑', idle: '○', ended: '✓', unrestored: '◌', unknown: '?' };
  const gateNames = { ready: '待认领', claimed: '已认领', submitted: '已交付', accepted: '已集成', paused: '已暂停' };
  const flowStages = [{ id: 'implementation', label: '认领与实现' }, { id: 'delivery', label: '交付' },
    { id: 'checks', label: '机械检查' }, { id: 'review', label: '独立审查' }, { id: 'integration', label: '集成' }];
  const flowColors = ['#58b9a7', '#b29af5', '#70a9f0', '#eda456', '#e685a6', '#78c98d'];

  function aggregate(states) {
    if (states.includes('waiting_user_answer')) return 'waiting_user_answer';
    if (states.includes('waiting_controller_answer')) return 'waiting_controller_answer';
    if (states.includes('running')) return 'running';
    if (!states.length || states.includes('unknown')) return 'unknown';
    if (states.includes('unrestored')) return 'unrestored';
    return states.includes('idle') ? 'idle' : 'ended';
  }

  // ---------- 预设数据（全部虚构） ----------
  // 出厂默认与 workbench/src/executionSettings.ts 的 factoryExecution 相同。
  const executionLabels = { worker: 'Worker', reviewer: '审查员', monitor: '监视器', ideation: '构思主控', executor: '执行主控' };
  const codexFactory = { model: 'gpt-6.1-sol', effort: 'high', fast: false }, claudeFactory = { model: 'claude-haiku-5-5', effort: 'low', fast: false };
  const initialData = () => ({
    execution: { worker: { ...codexFactory }, reviewer: { ...codexFactory }, monitor: { ...codexFactory }, ideation: { ...claudeFactory }, executor: { ...claudeFactory } },
    projects: [
      { id: 'inkwell', repo: '~/work/inkwell', git: { branch: 'main', upstream: true, ahead: 2, behind: 0 }, tasks: [
        { id: 'T-12', title: '导出页支持按标签筛选', state: 'claimed', attempt: '7d41c0aa', stage: 'implementation' },
        { id: 'T-11', title: '导入时保留原始时间戳', state: 'submitted', attempt: 'c2e90b17', candidate: 'a81d3c0f52', verification: 'running', stage: 'review',
          returns: ['checks', 'review'] },
        { id: 'T-14', title: '移除旧版配置迁移', state: 'claimed', attempt: '51ab6e02', stage: 'implementation' },
        { id: 'T-09', title: '修正 CSV 字段转义', state: 'accepted', attempt: '0e7f3a91', candidate: '4c2d9e1a77', verification: 'passed', integration: 'completed',
          stage: 'integration', integrated: true, returns: ['checks'] },
      ] },
      { id: 'tidepool', repo: '~/work/tidepool', git: { branch: 'feat/sync', upstream: true, ahead: 0, behind: 3 }, tasks: [
        { id: 'T-3', title: '离线队列重试改为指数退避', state: 'paused', attempt: '9b07d2c4', stage: null },
        { id: 'T-5', title: '梳理同步模块的现有行为', state: 'claimed', attempt: '3c58e1f0', stage: 'implementation' },
      ] },
      { id: 'ledger-cli', repo: '~/work/ledger-cli', git: { branch: 'main', upstream: false }, tasks: [
        { id: 'T-1', title: '初始化命令行参数解析', state: 'ready', stage: null },
      ] },
    ],
    // parent 只来自启动记录；没有父记录的会话进“未归属”。
    agents: [
      { id: 'launch-41c7', project: 'inkwell', task: 'T-12', attempt: null, parent: null, role: 'controller', preset: 'ideation', cli: 'claude', state: 'waiting_user_answer' },
      { id: 'launch-8e02', project: 'inkwell', task: 'T-12', attempt: null, parent: 'launch-41c7', role: 'controller', preset: 'executor', cli: 'claude', state: 'running' },
      { id: 'launch-a3f9', project: 'inkwell', task: 'T-12', attempt: 'a2', parent: 'launch-8e02', role: 'worker', cli: 'codex', state: 'running' },
      { id: 'launch-c611', project: 'inkwell', task: 'T-12', attempt: 'a2', parent: 'launch-8e02', role: 'monitor', cli: 'codex', state: 'idle' },
      { id: 'launch-2a6e', project: 'inkwell', task: 'T-11', attempt: 'a1', parent: 'launch-8e02', role: 'worker', cli: 'codex', state: 'idle' },
      { id: 'launch-5d20', project: 'inkwell', task: 'T-11', attempt: 'a1', parent: 'launch-8e02', role: 'reviewer', cli: 'codex', state: 'running' },
      { id: 'launch-e7b4', project: 'inkwell', task: 'T-14', attempt: 'a1', parent: 'launch-8e02', role: 'worker', cli: 'codex', state: 'waiting_controller_answer' },
      { id: 'launch-0b9d', project: 'inkwell', task: 'T-09', attempt: 'a1', parent: null, role: 'worker', cli: 'codex', state: 'ended' },
      { id: 'launch-62aa', project: 'tidepool', task: 'T-3', attempt: null, parent: null, role: 'controller', preset: 'ideation', cli: 'claude', state: 'running' },
      { id: 'launch-93fe', project: 'tidepool', task: 'T-3', attempt: null, parent: 'launch-62aa', role: 'controller', preset: 'executor', cli: 'claude', state: 'unrestored' },
      { id: 'launch-1d85', project: 'tidepool', task: 'T-3', attempt: 'a1', parent: 'launch-93fe', role: 'worker', cli: 'codex', state: 'unrestored' },
      { id: 'launch-f40c', project: 'tidepool', task: 'T-3', attempt: 'a1', parent: 'launch-93fe', role: 'reviewer', cli: 'codex', state: 'unknown' },
      ...['b1', 'b2', 'b3', 'b4', 'b5', 'b6'].map((suffix, index) => ({ id: 'launch-5e' + suffix, project: 'tidepool', task: 'T-5', attempt: 'a1',
        parent: 'launch-93fe', role: 'worker', cli: 'codex', state: index === 2 ? 'idle' : 'running' })),
      { id: 'launch-7a31', project: 'tidepool', task: 'T-5', attempt: 'a1', parent: null, role: 'monitor', cli: 'codex', state: 'idle' },
    ],
    questions: [
      { id: 'q-1', launch: 'launch-41c7', target: 'user', cli: 'claude', status: 'waiting', question: '导出时，已归档的条目默认要不要包含在内？',
        options: [{ label: '不包含', description: '与列表页的默认筛选一致' }, { label: '包含', description: '导出更完整，但和列表页看到的不一样' }],
        reply: ['● 收到：默认不包含已归档条目。', '● 已写进 T-12 任务卡的目标，ready_rev 加 1，通知执行主控。'] },
      { id: 'q-2', launch: 'launch-e7b4', target: 'controller', cli: 'codex', status: 'waiting', question: '旧版 0.8 的配置文件还需要能迁移吗？',
        options: [{ label: '不再支持', description: '删除迁移代码，在更新说明里写明' }, { label: '保留一个版本', description: '下个版本再删' }],
        reply: ['› 按答复继续：删除 0.8 迁移代码，更新说明里写明。'] },
    ],
  });

  const lines = {
    'launch-41c7': [['dim', '~/work/inkwell · claude'], ['', '> 导出页想加个按标签筛选'], ['', '● 先问清范围：只筛当前页，还是也影响导出文件？'],
      ['', '● 已写好 T-12 的任务卡：目标、非目标、允许修改的路径、完成条件'], ['', '● 标记就绪，交给执行主控派发'], ['warn', '● 还有一个默认行为要你定，见上方提问']],
    'launch-8e02': [['dim', '~/work/inkwell · claude'], ['', '› 收到 T-12（ready_rev 1）'], ['', '› 派发 worker：codex，attempt a2'], ['', '› 派发监视器：只读观察 T-12'],
      ['', '› T-11 已交付，新开只读审查会话'], ['', '› T-14 的 worker 在问迁移范围，正在看任务卡的非目标']],
    'launch-a3f9': [['dim', '~/work/inkwell/.worktrees/T-12-a2 · codex'], ['', '› 读取任务卡 T-12'], ['dim', '  允许修改：src/export/  tests/export/'],
      ['dim', '  验收文件：tests/export/test_tags.py（改动即拒收）'], ['', '› 先跑完成条件：python3 -m pytest tests/export'], ['warn', '  3 failed（红态，符合预期）'],
      ['', '› 实现标签筛选'], ['ok', '  12 passed'], ['', '› 提交并交付候选 7c90e3b，等待门禁检查']],
    'launch-c611': [['dim', 'monitor · codex'], ['', '› 观察 T-12 attempt a2'], ['dim', '  未发现越界写入；未发现重复派发']],
    'launch-2a6e': [['dim', '~/work/inkwell/.worktrees/T-11-a1 · codex'], ['', '› 第 1 次交付：机械检查打回（路径越界）'], ['', '› 第 2 次交付：审查打回（时区边界未覆盖）'],
      ['', '› 第 3 次交付 a81d3c0f52'], ['dim', '  等待独立审查结果']],
    'launch-5d20': [['dim', 'T-11-a1-review-3（一次性副本，断网）· codex'], ['', '› 审查候选 a81d3c0f52'], ['', '› 完成条件够不够格：覆盖夏令时切换日'],
      ['ok', '  变异 1：去掉时区换算 → 测试失败，抓到了'], ['ok', '  变异 2：时间戳截到分钟 → 测试失败，抓到了'], ['', '› 正在写审查报告']],
    'launch-e7b4': [['dim', '~/work/inkwell/.worktrees/T-14-a1 · codex'], ['', '› 读取任务卡 T-14'], ['', '› 发现 0.8 配置仍有迁移入口，任务卡没写要不要保留'], ['warn', '› 向主控提问，等待回答']],
    'launch-62aa': [['dim', '~/work/tidepool · claude'], ['', '● 整理 T-3 暂停的原因：执行主控重启后未恢复'], ['', '● 等执行主控按中断恢复流程回收后再派发']],
    'launch-93fe': [['dim', '~/work/tidepool · claude']],
    'launch-1d85': [['dim', '~/work/tidepool/.worktrees/T-3-a1 · codex']],
    'launch-f40c': [['dim', 'T-3-a1-review-1 · codex'], ['dim', '（当前回合状态无法核实，显示为未知）']],
  };
  const restoreErrors = {
    'launch-93fe': '未恢复：原生会话不存在。启动记录已保留。',
    'launch-1d85': '未恢复：受管 worker 未续接；请由执行主控按中断恢复流程回收后重新认领。启动记录已保留。',
  };
  const shellLines = cwd => [['', `${cwd} % git status -sb`], ['', cwd === '~' ? 'fatal: not a git repository' : '## main...origin/main [ahead 2]'], ['', `${cwd} % `]];

  // ---------- 界面状态 ----------
  let data, ui, layouts, panes, paneSeq, timers = [];
  function reset() {
    timers.forEach(clearTimeout); timers = [];
    data = initialData();
    ui = { project: 'inkwell', task: 'T-12', page: 'terminal', focusedAgent: null, focusedPane: null, collapsed: new Set(),
      notifications: true, dockBadges: true, menu: null, renaming: null, zoom: null, directory: 'home', settingsOpen: false, execRole: 'worker', execDraft: null, execMessage: '',
      flowOpen: {}, flowExpanded: {}, drafts: {} };
    panes = {}; layouts = {}; paneSeq = 0;
    const agentPane = launch => { const key = 'p' + (++paneSeq); panes[key] = { kind: 'agent', launch, lines: (lines[launch] || [['dim', '（演示没有为这个会话预设输出）']]).slice(), forward: false }; return key; };
    const shellPane = (cwd, label) => { const key = 'p' + (++paneSeq); panes[key] = { kind: 'shell', cwd, lines: shellLines(cwd), forward: false, project: label }; return key; };
    layouts['inkwell/T-12'] = { direction: 'right', first: agentPane('launch-41c7'), second: { direction: 'down', first: agentPane('launch-8e02'), second: agentPane('launch-a3f9') } };
    layouts['inkwell/T-11'] = { direction: 'right', first: agentPane('launch-2a6e'), second: agentPane('launch-5d20') };
    layouts['inkwell/T-14'] = agentPane('launch-e7b4');
    layouts['inkwell/T-09'] = null;
    layouts['tidepool/T-3'] = { direction: 'down', first: { direction: 'right', first: agentPane('launch-62aa'), second: agentPane('launch-93fe') },
      second: { direction: 'right', first: agentPane('launch-1d85'), second: agentPane('launch-f40c') } };
    layouts['tidepool/T-5'] = null;
    layouts['ledger-cli/T-1'] = null;
    layouts.free = shellPane('~', null);
    ui.makeAgentPane = agentPane; ui.makeShellPane = shellPane;
  }

  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  const icon = state => `<span class="status-icon" aria-hidden="true">${statusIcons[state] || '?'}</span>`;
  const findProject = id => data.projects.find(project => project.id === id);
  const findTask = () => findProject(ui.project)?.tasks.find(task => task.id === ui.task) || null;
  const findAgent = id => data.agents.find(agent => agent.id === id);
  const layoutKey = () => ui.task ? `${ui.project}/${ui.task}` : 'free';
  const roleLabel = agent => agent.role === 'controller' ? (agent.preset === 'ideation' ? '构思主控' : '执行主控')
    : { worker: 'worker', reviewer: '审查员', monitor: '监视器' }[agent.role];
  const paneRole = pane => {
    if (pane.kind === 'shell') return '普通终端';
    const agent = findAgent(pane.launch);
    return agent.role === 'controller' ? roleLabel(agent) : { worker: '受管 worker', reviewer: '独立审查', monitor: 'monitor' }[agent.role];
  };
  const descendants = id => data.agents.filter(child => child.parent === id).flatMap(child => [child, ...descendants(child.id)]);
  const openQuestions = launch => data.questions.filter(question => question.launch === launch && !['answered', 'cancelled'].includes(question.status));
  const notices = () => ui.notifications ? data.agents.filter(agent => agent.state === 'waiting_user_answer') : [];

  // ---------- 侧栏 ----------
  function projectRow(project) {
    const state = aggregate(data.agents.filter(agent => agent.project === project.id).map(agent => agent.state));
    const git = project.git.upstream ? `领先 ${project.git.ahead} / 落后 ${project.git.behind}` : '未设置上游';
    return `<button class="project-row" data-action="project" data-project-id="${esc(project.id)}" data-project-state="${state}" data-fk="project:${esc(project.id)}"
      ${ui.project === project.id ? 'aria-current="page"' : ''}>
      <span class="project-title">${icon(state)}${esc(project.id)}</span>
      <span class="project-git">${esc(project.git.branch)} · ${git}</span>
      <span class="project-state">${stateLabels[state]}</span>
      <span class="project-repo">${esc(project.repo)}</span></button>`;
  }
  function agentBranches(rows, level) {
    const projectAgents = data.agents.filter(agent => agent.project === ui.project);
    return `<ul class="agent-branches">${rows.map(agent => {
      const children = descendants(agent.id);
      const collapsed = ui.collapsed.has(agent.id);
      const summaryState = aggregate(children.map(child => child.state));
      const counts = Object.keys(stateLabels).filter(key => children.some(child => child.state === key))
        .map(key => `${stateLabels[key]} ${children.filter(child => child.state === key).length}`).join(' · ');
      const direct = projectAgents.filter(child => child.parent === agent.id);
      const controllers = direct.filter(child => child.role === 'controller');
      const tasks = [...new Set(direct.filter(child => child.role !== 'controller').map(child => child.task))];
      return `<li><div class="agent-line">
        ${children.length ? `<button class="agent-toggle" data-action="toggle-agent" data-agent-toggle="${agent.id}" data-fk="toggle:${agent.id}" aria-expanded="${!collapsed}"
          aria-controls="wb-children-${agent.id}" aria-label="${collapsed ? '展开' : '折叠'}${roleLabel(agent)}的子会话"><span aria-hidden="true">${collapsed ? '▸' : '▾'}</span></button>`
          : '<span class="agent-toggle-space" aria-hidden="true"></span>'}
        <button class="agent-row" data-action="agent" data-agent-launch="${agent.id}" data-agent-level="${level}" data-agent-state="${agent.state}" data-fk="agent:${agent.id}"
          ${ui.focusedAgent === agent.id ? 'aria-current="true"' : ''} ${collapsed ? `data-descendant-state="${summaryState}"` : ''}>
          <span class="agent-role">${icon(agent.state)}${roleLabel(agent)}</span>
          <span class="agent-state">${stateLabels[agent.state]}</span>
          <span class="agent-meta">${esc(agent.task)} · ${agent.attempt ? 'attempt ' + agent.attempt : '无 attempt'} · ${agent.cli}</span>
          ${collapsed ? `<span class="agent-subtree" data-agent-summary="${agent.id}">${icon(summaryState)}子会话 ${children.length} · ${counts}</span>` : ''}
        </button></div>
        <div id="wb-children-${agent.id}" ${collapsed ? 'hidden' : ''}>
          ${controllers.length ? agentBranches(controllers, level + 1) : ''}
          ${tasks.map(task => `<div class="agent-task-group"><div class="agent-task-label">任务 ${esc(task)}</div>
            ${agentBranches(direct.filter(child => child.task === task && child.role !== 'controller'), level + 1)}</div>`).join('')}
        </div></li>`;
    }).join('')}</ul>`;
  }
  function sidebar() {
    const rows = data.agents.filter(agent => agent.project === ui.project);
    const roots = rows.filter(agent => !agent.parent && agent.role === 'controller' && agent.preset === 'ideation');
    const orphans = rows.filter(agent => !agent.parent && !(agent.role === 'controller' && agent.preset === 'ideation'));
    return `<aside class="sidebar">
      <div class="brand">a2a <span>工作台</span></div>
      <div class="catalog-heading"><span class="nav-label">项目目录</span><button data-action="note" data-note="演示数据是固定的，刷新不会变化。" data-fk="refresh">刷新列表</button></div>
      <button class="create-project" data-action="note" data-note="真实应用会打开 macOS 的目录选择框，再填表单注册首个任务；演示里不打开。" data-fk="create-project">新增项目目录</button>
      <nav class="project-list" aria-label="项目目录" data-sk="projects">${data.projects.map(projectRow).join('')}</nav>
      <div class="catalog-heading agent-heading"><span class="nav-label">agent 会话</span></div>
      <nav class="agent-list" aria-label="agent 层级" data-sk="agents">
        ${ui.project ? agentBranches(roots, 0) : ''}
        ${orphans.length ? `<div class="unassigned-agents"><div class="agent-task-label">未归属</div>
          ${[...new Set(orphans.map(agent => agent.task))].map(task => `<div class="agent-task-group"><div class="agent-task-label">任务 ${esc(task)}</div>
            ${agentBranches(orphans.filter(agent => agent.task === task), 0)}</div>`).join('')}</div>` : ''}
        ${rows.length ? '' : `<p class="catalog-status">${ui.project ? '这个项目还没有 agent 启动记录。' : '选择项目，查看已有会话。'}</p>`}
      </nav>
      <button class="free-terminals" data-action="free" data-fk="free" ${!ui.project && !ui.task ? 'aria-current="page"' : ''}>独立终端</button>
      <details class="sidebar-settings" data-action-toggle="settings" ${ui.settingsOpen ? 'open' : ''}><summary data-fk="settings">图例与设置</summary>
        ${executionSettings()}
        <div class="status-legend">${Object.entries(stateLabels).map(([state, label]) => `<span>${icon(state)}${label}</span>`).join('')}</div>
        <fieldset class="notification-settings"><legend>应用内通知</legend>
          <label><input type="checkbox" data-setting="notifications" data-fk="setting:notifications" ${ui.notifications ? 'checked' : ''}>等待用户回答时提醒</label>
          <label><input type="checkbox" data-setting="dockBadges" data-fk="setting:dockBadges" ${ui.dockBadges ? 'checked' : ''}>后台时显示 Dock 待答数量</label>
        </fieldset>
      </details>
      <div class="sidebar-footer">原生 CLI · 本地编排</div>
    </aside>`;
  }

  // 会话模型设置（ExecutionSettings.tsx）：按角色保存，下次启动生效。
  function executionSettings() {
    const draft = ui.execDraft ?? data.execution[ui.execRole];
    return `<form class="execution-settings" aria-label="会话模型设置" data-execution>
      <strong>会话模型</strong>
      <label>角色<select data-exec-role data-fk="exec:role">${Object.entries(executionLabels).map(([key, label]) =>
        `<option value="${key}" ${ui.execRole === key ? 'selected' : ''}>${label}</option>`).join('')}</select></label>
      <label>模型<input data-exec-field="model" data-fk="exec:model" required value="${esc(draft.model)}"></label>
      <label>思考强度<input data-exec-field="effort" data-fk="exec:effort" required value="${esc(draft.effort)}"></label>
      <label class="execution-fast"><input type="checkbox" data-exec-field="fast" data-fk="exec:fast" ${draft.fast ? 'checked' : ''}>Fast</label>
      <p>填写当前 CLI 支持的模型和强度。主控派发时可覆盖；正在运行的会话保持原设置。</p>
      <button data-fk="exec:save">保存角色设置</button>
      ${ui.execMessage ? `<p role="status">${esc(ui.execMessage)}</p>` : ''}
    </form>`;
  }

  // ---------- 窗格 ----------
  function paneRects(tree, x = 0, y = 0, w = 100, h = 100) {
    if (!tree) return {};
    if (typeof tree === 'string') return { [tree]: { x, y, w, h } };
    return tree.direction === 'right'
      ? { ...paneRects(tree.first, x, y, w / 2, h), ...paneRects(tree.second, x + w / 2, y, w / 2, h) }
      : { ...paneRects(tree.first, x, y, w, h / 2), ...paneRects(tree.second, x, y + h / 2, w, h / 2) };
  }
  const replaceLeaf = (tree, key, next) => typeof tree === 'string' ? (tree === key ? next : tree)
    : tree && { ...tree, first: replaceLeaf(tree.first, key, next), second: replaceLeaf(tree.second, key, next) };
  function removeLeaf(tree, key) {
    if (typeof tree === 'string') return tree === key ? null : tree;
    if (!tree) return null;
    const first = removeLeaf(tree.first, key), second = removeLeaf(tree.second, key);
    return first && second ? { ...tree, first, second } : first || second;
  }

  function questionForm(question) {
    const draft = ui.drafts[question.id] ?? '';
    const sending = question.status === 'sending';
    return `<form class="native-question" data-question-id="${question.id}">
      <div class="question-heading"><strong>${question.target === 'controller' ? '等待主控回答' : '等待用户回答'}</strong>
        <span>${question.cli === 'claude' ? 'Claude Code' : 'Codex'} · 当前窗格</span></div>
      <fieldset ${sending ? 'disabled' : ''}><legend>${esc(question.question)}</legend>
        <div class="question-options">${question.options.map(option => `<button type="button" data-action="option" data-question="${question.id}" data-option="${esc(option.label)}"
          data-fk="option:${question.id}:${esc(option.label)}" aria-pressed="${draft === option.label}">${esc(option.label)}<small>${esc(option.description)}</small></button>`).join('')}</div>
        <label>补充或其他答复<input type="text" maxlength="4000" data-answer="${question.id}" data-fk="answer:${question.id}" value="${esc(draft)}"></label>
      </fieldset>
      ${sending ? '<p role="status">答复已送入窗格，等待原生确认。</p>' : ''}
      <button data-fk="send:${question.id}" ${sending || !draft.trim() ? 'disabled' : ''}>发送答复到窗格</button>
    </form>`;
  }

  function paneView(key, focused) {
    const pane = panes[key];
    const shell = pane.kind === 'shell';
    const agent = shell ? null : findAgent(pane.launch);
    const role = paneRole(pane);
    const name = pane.name;
    const readonly = !shell && (agent.role === 'reviewer' || agent.role === 'monitor' || ['unrestored', 'unknown', 'ended'].includes(agent.state));
    const activity = shell ? '运行中' : { running: '忙', waiting_user_answer: '忙', waiting_controller_answer: '忙', idle: '空闲' }[agent.state] ?? '未知';
    const identity = shell ? `${pane.project ?? '独立终端'} · ${pane.cwd}`
      : `${agent.role}${agent.preset ? '/' + agent.preset : ''} · task ${agent.task} · launch ${agent.id}${agent.attempt ? ' · attempt ' + agent.attempt : ''}`;
    const footer = shell ? '普通终端 · zsh' : agent.role === 'reviewer' ? '独立审查 · 只读' : agent.role === 'worker' ? '在此窗格输入会记录为人工介入' : '在此窗格输入会记录为用户输入';
    const lifecycle = shell ? '运行中' : agent.state === 'ended' ? '已结束' : agent.state === 'unknown' || agent.state === 'unrestored' ? '未知' : '运行中';
    return `<section class="pane${focused ? ' pane-focused' : ''}" data-pane-key="${key}" data-launch-id="${pane.launch ?? ''}" aria-label="${role}交互终端">
      ${!shell && restoreErrors[agent.id] ? `<div class="connection-error" role="alert">${esc(restoreErrors[agent.id])}</div>` : ''}
      <div class="pane-header"><strong title="${esc(name ?? role)}">${esc(name ?? role)}</strong>${name ? `<span>${role}</span>` : ''}
        <button class="pane-menu-trigger" data-action="menu" data-pane="${key}" data-fk="menu:${key}" aria-label="窗格菜单" aria-haspopup="menu" aria-expanded="${ui.menu?.pane === key}">⋯</button>
        <span>${shell ? 'zsh' : agent.cli === 'claude' ? '2.1.302 (Claude Code)' : 'codex-cli 0.163.0'}</span>
        <span class="readonly">${readonly ? '只读' : '可输入'}</span>
        <span class="input-target">${focused && !readonly ? '正在输入：' + role : '终端未聚焦'}</span>
        <span class="pane-state">${activity}</span>
        <button data-action="enter" data-pane="${key}" data-fk="enter:${key}" ${readonly ? 'disabled' : ''}>进入终端</button>
        <button data-action="close" data-pane="${key}" data-fk="close:${key}">关闭窗格</button>
        <span class="pane-identity">${esc(identity)}</span>
      </div>
      ${ui.renaming === key ? `<form class="pane-rename" data-rename="${key}"><label>窗格名称 <input data-rename-input="${key}" data-fk="rename:${key}" maxlength="100" value="${esc(ui.renameDraft)}"></label>
        <button data-fk="rename-save:${key}" ${ui.renameDraft.trim() ? '' : 'disabled'}>保存名称</button><button type="button" data-action="rename-cancel" data-fk="rename-cancel:${key}">取消</button></form>` : ''}
      <div class="questions-panel" aria-label="原生提问">${shell ? '' : openQuestions(agent.id).map(questionForm).join('')}</div>
      <div class="terminal-scroll" data-terminal="${key}" data-sk="term:${key}"><pre class="terminal-lines">${pane.lines.map(([kind, text]) =>
        kind ? `<span class="${kind}">${esc(text)}</span>` : esc(text)).join('\n')}</pre></div>
      <div class="pane-footer"><span>${footer}</span><span>执行：${lifecycle}</span></div>
    </section>`;
  }

  function menuView() {
    if (!ui.menu) return '';
    const pane = panes[ui.menu.pane];
    return `<div class="pane-menu" role="menu" aria-label="窗格操作" style="left:${ui.menu.x}px;top:${ui.menu.y}px">
      <button role="menuitem" data-action="rename" data-fk="mi:rename">重命名窗格</button>
      <button role="menuitem" data-action="split" data-direction="right" data-fk="mi:right">向右分屏</button>
      <button role="menuitem" data-action="split" data-direction="down" data-fk="mi:down">向下分屏</button>
      <button role="menuitem" data-action="zoom" data-fk="mi:zoom">${ui.zoom === ui.menu.pane ? '还原' : '放大'}</button>
      <button role="menuitemcheckbox" aria-checked="${pane.forward}" data-action="forward" data-fk="mi:forward">${pane.forward ? '✓ ' : ''}把右键发给窗格</button>
      <button role="menuitem" data-action="close" data-pane="${ui.menu.pane}" data-fk="mi:close">关闭窗格</button>
    </div>`;
  }

  function terminalPage() {
    const task = findTask();
    const project = findProject(ui.project);
    const layout = layouts[layoutKey()] ?? null;
    const rects = paneRects(layout);
    const keys = Object.keys(rects);
    return `<div class="terminal-page" ${ui.page !== 'terminal' ? 'hidden' : ''}>
      <header class="task-header"><div><div class="eyebrow">${task ? `${esc(ui.project)} / ${esc(task.id)}` : '终端工作区'}</div>
        <h1>${task ? esc(task.title) : '独立终端'}</h1></div><span class="connection">演示数据 · 未连接后台</span></header>
      ${project ? `<nav class="task-strip" aria-label="项目任务" data-sk="tasks"><button class="create-task" data-action="note" data-fk="create-task"
          data-note="真实应用会打开新建任务表单，注册时走门禁的任务卡校验；演示里不打开。">新建任务</button>
        ${project.tasks.map(item => `<button class="task-row" data-action="task" data-task-option="${item.id}" data-fk="task:${item.id}" ${task && task.id === item.id ? 'aria-current="page"' : ''}>
          <span class="task-title">${esc(item.title)}</span><span class="task-meta">${item.id} · ${gateNames[item.state]}</span></button>`).join('')}</nav>` : ''}
      <div class="pane-toolbar"><span role="status">新建或分屏，打开你自己的 zsh</span>
        <label class="directory-choice">工作目录 <select aria-label="终端工作目录" data-directory data-fk="directory">
          <option value="home" ${ui.directory === 'home' ? 'selected' : ''}>家目录</option>${task ? `<option value="project" ${ui.directory === 'project' ? 'selected' : ''}>项目目录</option>` : ''}</select></label>
        <button data-action="new-terminal" data-fk="new-terminal">新建终端</button></div>
      <div class="pane-layout" aria-label="终端窗格">
        ${keys.map(key => {
          const rect = ui.zoom === key ? { x: 0, y: 0, w: 100, h: 100 } : rects[key];
          return `<div class="pane-slot" ${ui.zoom && ui.zoom !== key ? 'hidden' : ''} style="left:${rect.x}%;top:${rect.y}%;width:${rect.w}%;height:${rect.h}%">${paneView(key, ui.focusedPane === key)}</div>`;
        }).join('')}
        ${keys.length ? '' : task ? '<p class="selection-hint">当前任务没有打开的窗格。</p>'
          : '<div class="selection-hint"><h2>打开终端或选择任务</h2><p>选择项目下的任务，查看它的会话和门禁状态。</p></div>'}
      </div>
      ${task ? `<section class="gate" aria-label="门禁状态"><div><span class="eyebrow">当前任务门禁</span><strong>${gateNames[task.state]}</strong></div>
        <dl><div><dt>执行尝试</dt><dd>${task.attempt ?? '尚未认领'}</dd></div><div><dt>候选提交</dt><dd>${task.candidate ?? '尚未交付'}</dd></div>
          <div><dt>验收</dt><dd>${task.verification ?? '尚未开始'}</dd></div><div><dt>集成</dt><dd>${task.integration ?? '尚未开始'}</dd></div></dl></section>` : ''}
    </div>`;
  }

  // ---------- 流程页 ----------
  function capsules(list, group) {
    const expanded = ui.flowExpanded[group];
    return `<div class="flow-agents">${(expanded ? list : list.slice(0, 4)).map((agent, index) => `<div class="flow-agent" data-flow-agent="${agent.id}" data-flow-state="${agent.state}">
        <span class="flow-dot" aria-hidden="true" style="background:${flowColors[index % flowColors.length]}"></span>
        <span><strong>${agent.id}</strong><small>${roleLabel(agent)} · ${agent.cli} · ${agent.attempt ?? 'attempt 未知'}</small>
          <small><span aria-hidden="true">${statusIcons[agent.state]}</span> ${stateLabels[agent.state]}</small></span></div>`).join('')}
      ${list.length > 4 ? `<button class="flow-more" data-action="flow-more" data-group="${group}" data-flow-more="${group}" data-fk="more:${group}" aria-expanded="${Boolean(expanded)}">${expanded ? '收起' : `还有 ${list.length - 4} 个 ↗`}</button>` : ''}
    </div>`;
  }
  function flowPage() {
    const lanes = data.projects.flatMap(project => project.tasks.map(task => ({ project: project.id, task })));
    const live = agent => agent.state !== 'ended';
    const unassigned = data.agents.filter(agent => !agent.parent && !(agent.role === 'controller' && agent.preset === 'ideation') && live(agent));
    return `<section class="flow-page" aria-label="系统流程" data-sk="flow-page">
      <div class="flow-intro"><h2>系统流程</h2><p>一张票一条泳道 · 阶段来自门禁记录 · agent 只按已保存的归属展示</p>
        <p class="flow-legend">● 运行中　◐ 等待用户回答　◑ 等待主控回答　○ 空闲　✓ 已结束　◌ 未恢复　? 未知</p></div>
      <div class="flow-scroll" tabindex="0" aria-label="任务泳道，可左右滚动" data-sk="flow-scroll">
        ${lanes.map(({ project, task }) => {
          const open = ui.flowOpen[task.id] ?? !task.integrated;
          const current = flowStages.findIndex(stage => stage.id === task.stage);
          const laneAgents = data.agents.filter(agent => agent.task === task.id && agent.parent && agent.attempt && live(agent));
          const monitors = laneAgents.filter(agent => agent.role === 'monitor');
          const returns = task.returns ?? [];
          return `<article class="flow-lane" data-flow-task="${task.id}" data-flow-stage="${task.stage ?? 'unknown'}">
            <header class="flow-lane-heading"><button data-action="flow-toggle" data-task="${task.id}" data-flow-toggle="${task.id}" data-fk="lane:${task.id}" aria-expanded="${open}">
              <span aria-hidden="true">${open ? '⌄' : '›'}</span> ${task.id} · ${esc(task.title)}</button>
              <span>${project} · ${task.integrated ? '已集成' : current < 0 ? '阶段未知 · 核对门禁记录' : flowStages[current].label}${returns.length ? ` · 打回 ${returns.length} 次` : ''}</span></header>
            ${open ? `<div class="flow-lane-body">
              ${monitors.length ? `<div class="flow-monitors"><span>贯穿监视</span>${capsules(monitors, task.id + '-monitors')}</div>` : ''}
              <div class="flow-stages">
                ${returns.length ? `<div class="flow-returns" aria-label="打回 ${returns.length} 次">${['checks', 'review'].map(from => {
                  const n = returns.filter(item => item === from).length;
                  return n ? `<div class="flow-return from-${from}" data-flow-return="${from}" data-return-count="${n}"><span>↶ ${from === 'review' ? '审查' : '机械检查'}打回 ${n} 次</span></div>` : '';
                }).join('')}</div>` : ''}
                ${flowStages.map((stage, index) => `<section data-flow-column="${stage.id}" class="flow-stage ${task.integrated || index < current ? 'complete' : index === current ? 'current' : ''}"
                  aria-label="${stage.label}" ${index === current && !task.integrated ? 'aria-current="step"' : ''}>
                  <div class="flow-track" aria-hidden="true"><i></i>${index < flowStages.length - 1 ? '<span>›››</span>' : ''}</div>
                  <h3>${stage.label}</h3>
                  ${capsules(laneAgents.filter(agent => agent.role !== 'monitor' && stage.id === (agent.role === 'reviewer' ? 'review' : 'implementation')), task.id + '-' + stage.id)}
                </section>`).join('')}
              </div></div>` : ''}
          </article>`;
        }).join('')}
      </div>
      ${unassigned.length ? `<section class="flow-unassigned" aria-label="未归属"><h3>未归属</h3>
        <p>父记录、任务或当前 attempt 无法对应，或角色不属于票内阶段的会话。</p>${capsules(unassigned, 'unassigned')}</section>` : ''}
    </section>`;
  }

  // ---------- 整体渲染 ----------
  function render() {
    const active = document.activeElement && root.contains(document.activeElement) ? document.activeElement.getAttribute('data-fk') : null;
    const scrolls = {};
    root.querySelectorAll('[data-sk]').forEach(el => { scrolls[el.dataset.sk] = [el.scrollTop, el.scrollLeft]; });
    const pending = notices();
    const waiting = data.agents.filter(agent => agent.state === 'waiting_user_answer').length;
    root.innerHTML = `<div class="wb-titlebar"><i aria-hidden="true"></i><i aria-hidden="true"></i><i aria-hidden="true"></i><span>a2a 工作台（演示）</span>
        <output data-dock aria-label="Dock 角标">${ui.dockBadges && waiting ? `Dock 角标 <b>${waiting}</b>` : ''}</output></div>
      <div class="workbench">${sidebar()}
        <main>
          <nav class="workspace-pages" aria-label="工作区页面">
            <button data-action="page" data-page="terminal" data-fk="page:terminal" ${ui.page === 'terminal' ? 'aria-current="page"' : ''}>终端</button>
            <button data-action="page" data-page="flow" data-flow-tab data-fk="page:flow" ${ui.page === 'flow' ? 'aria-current="page"' : ''}>流程</button>
          </nav>
          ${ui.page === 'flow' ? flowPage() : ''}
          ${terminalPage()}
        </main></div>
      <aside class="app-notifications" aria-label="待回答通知" aria-live="polite">${pending.map(agent => `<button data-action="notice" data-notice-launch="${agent.id}" data-fk="notice:${agent.id}">
        <strong>等待用户回答</strong><span>${agent.project} · ${roleLabel(agent)}</span><span>${agent.task ?? '未归属任务'} · 查看问题 →</span></button>`).join('')}</aside>
      ${menuView()}
      <p class="wb-note" role="status" data-note-out>${esc(ui.note ?? '')}</p>`;
    root.querySelectorAll('[data-sk]').forEach(el => { const saved = scrolls[el.dataset.sk]; if (saved) { el.scrollTop = saved[0]; el.scrollLeft = saved[1]; } });
    if (ui.menu) root.querySelector('.pane-menu button')?.focus();
    else if (ui.renaming && ui.renameFresh) { const input = root.querySelector('[data-rename-input]'); input?.focus(); input?.select(); ui.renameFresh = false; }
    else if (ui.focusTarget) { root.querySelector(`[data-fk="${ui.focusTarget}"]`)?.focus(); ui.focusTarget = null; }
    else if (active) root.querySelector(`[data-fk="${CSS.escape(active)}"]`)?.focus();
    root.dataset.ready = 'true';
  }

  // ---------- 交互 ----------
  function selectAgent(id) {
    const agent = findAgent(id);
    ui.project = agent.project; ui.task = agent.task; ui.page = 'terminal'; ui.focusedAgent = id; ui.zoom = null; ui.menu = null;
    const key = layoutKey();
    let paneKey = Object.keys(paneRects(layouts[key])).find(k => panes[k].launch === id);
    if (!paneKey) { // 真实应用的 selectAgent 会打开该会话的窗格；演示里按向下分屏加入。
      paneKey = ui.makeAgentPane(id);
      layouts[key] = layouts[key] ? { direction: 'down', first: layouts[key], second: paneKey } : paneKey;
    }
    ui.focusedPane = paneKey;
  }
  function openMenu(pane, clientX, clientY) {
    const box = root.getBoundingClientRect();
    ui.menu = { pane, x: Math.max(4, Math.min(clientX - box.left, box.width - 218)), y: Math.max(4, Math.min(clientY - box.top, box.height - 280)) };
    ui.menuReturn = 'menu:' + pane;
  }
  function closeMenu() { if (!ui.menu) return; ui.focusTarget = ui.menuReturn; ui.menu = null; }
  function closePane(key) {
    const layoutId = layoutKey();
    layouts[layoutId] = removeLeaf(layouts[layoutId], key);
    if (ui.zoom === key) ui.zoom = null;
    if (ui.focusedPane === key) ui.focusedPane = null;
    ui.menu = null;
    delete panes[key];
  }
  function answer(questionId) {
    const question = data.questions.find(item => item.id === questionId);
    const value = (ui.drafts[questionId] ?? '').trim();
    if (!value || question.status !== 'waiting') return;
    question.status = 'sending';
    const paneKey = Object.keys(panes).find(key => panes[key].launch === question.launch);
    render();
    timers.push(setTimeout(() => {
      question.status = 'answered';
      const agent = findAgent(question.launch);
      agent.state = 'running';
      if (paneKey && panes[paneKey]) panes[paneKey].lines.push(['info', '› ' + value], ...question.reply.map(text => ['', text]));
      ui.note = `${roleLabel(agent)}已收到答复，状态回到“运行中”。`;
      render();
    }, 900));
  }

  root.addEventListener('click', event => {
    const target = event.target.closest('[data-action]');
    if (!target || target.disabled || !root.contains(target)) {
      if (ui.menu && !event.target.closest('.pane-menu')) { ui.menu = null; render(); }
      return;
    }
    const action = target.dataset.action;
    const paneKey = target.dataset.pane ?? ui.menu?.pane;
    ui.note = null;
    switch (action) {
      case 'project': {
        const project = findProject(target.dataset.projectId);
        Object.assign(ui, { project: project.id, task: project.tasks[0]?.id ?? null, focusedAgent: null, focusedPane: null, page: 'terminal', zoom: null, menu: null });
        break;
      }
      case 'task': Object.assign(ui, { task: target.dataset.taskOption, focusedPane: null, focusedAgent: null, zoom: null, menu: null }); break;
      case 'free': Object.assign(ui, { project: null, task: null, focusedAgent: null, focusedPane: null, page: 'terminal', zoom: null, menu: null, directory: 'home' }); break;
      case 'toggle-agent': {
        const id = target.dataset.agentToggle;
        if (ui.collapsed.has(id)) ui.collapsed.delete(id); else ui.collapsed.add(id);
        break;
      }
      case 'agent': case 'notice': selectAgent(target.dataset.agentLaunch ?? target.dataset.noticeLaunch); break;
      case 'page': ui.page = target.dataset.page; ui.menu = null; break;
      case 'menu':
        if (ui.menu?.pane === paneKey) closeMenu();
        else { const rect = target.getBoundingClientRect(); openMenu(paneKey, rect.left, rect.bottom); }
        break;
      case 'rename': ui.renaming = paneKey; ui.renameDraft = panes[paneKey].name ?? paneRole(panes[paneKey]); ui.renameFresh = true; ui.menu = null; break;
      case 'rename-cancel': ui.focusTarget = 'menu:' + ui.renaming; ui.renaming = null; break;
      case 'split': {
        const next = ui.makeShellPane(ui.task ? findProject(ui.project).repo : '~', ui.project);
        const layoutId = layoutKey();
        layouts[layoutId] = replaceLeaf(layouts[layoutId], paneKey, { direction: target.dataset.direction, first: paneKey, second: next });
        ui.zoom = null; ui.focusTarget = 'menu:' + paneKey; ui.menu = null;
        break;
      }
      case 'zoom': ui.zoom = ui.zoom === paneKey ? null : paneKey; closeMenu(); break;
      case 'forward': panes[paneKey].forward = !panes[paneKey].forward; closeMenu(); break;
      case 'close': closePane(paneKey); ui.note = '窗格已关闭。'; break;
      case 'enter': ui.focusedPane = paneKey; ui.note = '演示里的终端不接收键盘输入。'; break;
      case 'new-terminal': {
        const cwd = ui.directory === 'project' && ui.task ? findProject(ui.project).repo : '~';
        const next = ui.makeShellPane(cwd, ui.task ? ui.project : null);
        const layoutId = layoutKey();
        layouts[layoutId] = layouts[layoutId] ? { direction: 'right', first: layouts[layoutId], second: next } : next;
        ui.zoom = null;
        break;
      }
      case 'option': ui.drafts[target.dataset.question] = target.dataset.option; break;
      case 'flow-toggle': ui.flowOpen[target.dataset.task] = target.getAttribute('aria-expanded') !== 'true'; break;
      case 'flow-more': ui.flowExpanded[target.dataset.group] = !ui.flowExpanded[target.dataset.group]; break;
      case 'note': ui.note = target.dataset.note; break;
      default: return;
    }
    render();
  });

  root.addEventListener('contextmenu', event => {
    const pane = event.target.closest('.pane');
    if (!pane) return;
    event.preventDefault();
    const key = pane.dataset.paneKey;
    if (panes[key].forward && event.target.closest('.terminal-scroll')) {
      panes[key].lines.push(['dim', '（右键已作为鼠标事件发给窗格里的程序）']);
      ui.menu = null; render();
      return;
    }
    openMenu(key, event.clientX, event.clientY); render();
  });

  root.addEventListener('submit', event => {
    event.preventDefault();
    const form = event.target;
    if (form.dataset.questionId) answer(form.dataset.questionId);
    else if (form.hasAttribute('data-execution')) {
      data.execution[ui.execRole] = { ...(ui.execDraft ?? data.execution[ui.execRole]) };
      ui.execDraft = null; ui.execMessage = '已保存，下次启动生效'; render();
    }
    else if (form.dataset.rename) {
      const key = form.dataset.rename;
      if (!ui.renameDraft.trim()) return;
      panes[key].name = ui.renameDraft.trim(); ui.renaming = null; ui.focusTarget = 'menu:' + key; render();
    }
  });

  root.addEventListener('input', event => {
    const el = event.target;
    if (el.dataset.answer) {
      ui.drafts[el.dataset.answer] = el.value;
      el.closest('form').querySelectorAll('[aria-pressed]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.option === el.value)));
      el.closest('form').querySelector(':scope > button').disabled = !el.value.trim();
    } else if (el.dataset.execField && el.type !== 'checkbox') {
      ui.execDraft = { ...(ui.execDraft ?? data.execution[ui.execRole]), [el.dataset.execField]: el.value };
    } else if (el.dataset.renameInput) {
      ui.renameDraft = el.value;
      el.closest('form').querySelector('button:not([type])').disabled = !el.value.trim();
    }
  });

  root.addEventListener('change', event => {
    const el = event.target;
    if (el.dataset.setting) { ui[el.dataset.setting] = el.checked; render(); }
    else if (el.hasAttribute('data-exec-role')) { ui.execRole = el.value; ui.execDraft = null; ui.execMessage = ''; render(); }
    else if (el.dataset.execField === 'fast') ui.execDraft = { ...(ui.execDraft ?? data.execution[ui.execRole]), fast: el.checked };
    else if (el.hasAttribute('data-directory')) ui.directory = el.value;
  });
  root.addEventListener('toggle', event => { if (event.target.matches('.sidebar-settings')) ui.settingsOpen = event.target.open; }, true);

  root.addEventListener('keydown', event => {
    if (ui.menu && event.target.closest('.pane-menu')) {
      const items = [...root.querySelectorAll('.pane-menu button')];
      const index = items.indexOf(document.activeElement);
      if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
        event.preventDefault();
        items[event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
      } else if (event.key === 'Escape' || event.key === 'Tab') { event.preventDefault(); closeMenu(); render(); }
    } else if (event.key === 'Escape' && event.target.dataset.renameInput) {
      ui.focusTarget = 'menu:' + ui.renaming; ui.renaming = null; render();
    }
  });

  // 页面上的“分步引导”和“重置演示”按钮。
  document.querySelectorAll('[data-demo-go]').forEach(button => button.addEventListener('click', () => {
    const go = button.dataset.demoGo;
    ui.menu = null; ui.note = null;
    if (go === 'reset') { reset(); render(); ui.focusTarget = null; root.closest('.demo-canvas')?.scrollTo({ left: 0 }); return; }
    if (go === 'question') { const waiting = data.agents.find(agent => agent.state === 'waiting_user_answer') ?? findAgent('launch-41c7'); selectAgent(waiting.id); }
    if (go === 'menu' || go === 'terminal') ui.page = 'terminal';
    if (go === 'flow') ui.page = 'flow';
    const focus = { question: '[data-question-id] button[data-action="option"]', menu: '.pane-menu-trigger', flow: '[data-flow-tab]', sidebar: '.project-row' }[go];
    render();
    const el = root.querySelector(focus);
    if (el) {
      const canvas = root.closest('.demo-canvas');
      const offset = el.getBoundingClientRect().left - canvas.getBoundingClientRect().left + canvas.scrollLeft;
      canvas.scrollTo({ left: Math.max(0, offset - 24) });
      root.scrollIntoView({ block: 'nearest' });
      el.focus({ preventScroll: true });
    }
  }));

  reset();
  render();
})();
