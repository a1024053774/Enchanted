// Enchanted 产品页的工作台演示：全部是预设的虚构数据，不连后台、不调模型。
// 结构与文案取自 workbench/app 的 renderer.tsx、FlowPage.tsx、QuestionsPanel.tsx、AppNotifications.tsx、
// IssuesPage.tsx、RecordsPage.tsx、MetricsPage.tsx、ReflectPage.tsx、RetrospectiveSections.tsx，
// 状态优先级取自 workbench/src/sidebar.ts，阶段取自 workbench/src/flowStages.ts，复盘默认值取自 workbench/src/retrospective.ts。
// 页面上每个分功能展示经 window.EnchantedDemo.mount(窗口元素) 挂一份演示，再用 go(场景名) 切换状态，见 showcase.js。
(() => {
  'use strict';
  // 页面上有多个分功能展示，每个展示各自挂一份演示：数据、界面状态和计时器都在 mount 里，互不影响。
  function mount(root) {

    const stateLabels = { running: '运行中', waiting_user_answer: '等你回答', waiting_controller_answer: '等主控回答',
      idle: '空闲', ended: '已结束', unrestored: '未恢复', unknown: '未知' };
    // 与 renderer.tsx 的 glyphs 相同的 16×16 图形。
    const glyphs = {
      running: '<circle class="glyph-spin" cx="8" cy="8" r="5.6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-dasharray="26 10"/>',
      waiting_user_answer: '<circle cx="8" cy="8" r="5.8" fill="none" stroke="currentColor" stroke-width="1.6"/><circle cx="8" cy="8" r="2.8" fill="currentColor"/>',
      waiting_controller_answer: '<circle cx="8" cy="8" r="5.8" fill="none" stroke="currentColor" stroke-width="1.6" stroke-dasharray="3 2.4"/>',
      idle: '<path d="M3.8 8.4 6.6 11 12.2 5.2" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
      ended: '<path d="M10.9 11.6A5 5 0 0 1 6.4 3.1a5.2 5.2 0 1 0 6.6 6.6 5 5 0 0 1-2.1 1.9Z" fill="currentColor"/>',
      unrestored: '<circle cx="8" cy="8" r="5.8" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M4 12 12 4" stroke="currentColor" stroke-width="1.5"/>',
      unknown: '<circle cx="8" cy="8" r="2.2" fill="currentColor"/>',
    };
    const svg = (body, w = 16, h = 16) => `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true">${body}</svg>`;
    const svgSidebar = svg('<rect x="1.5" y="1.5" width="15" height="13" rx="3" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M6.5 2v12" stroke="currentColor" stroke-width="1.4"/>', 18, 16);
    const svgGear = svg('<circle cx="8" cy="8" r="2.2" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M8 1.6v1.8M8 12.6v1.8M1.6 8h1.8M12.6 8h1.8M3.5 3.5l1.3 1.3M11.2 11.2l1.3 1.3M3.5 12.5l1.3-1.3M11.2 4.8l1.3-1.3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>');
    const svgPlus = svg('<path d="M8 2.5v11M2.5 8h11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>');
    const svgClose = svg('<path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>');
    const svgDots = svg('<circle cx="3.5" cy="8" r="1.3" fill="currentColor"/><circle cx="8" cy="8" r="1.3" fill="currentColor"/><circle cx="12.5" cy="8" r="1.3" fill="currentColor"/>');
    const chevron = collapsed => svg(`<path d="${collapsed ? 'M6 3.5 10.5 8 6 12.5' : 'M3.5 6 8 10.5 12.5 6'}" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>`, 16, 16).replace('width="16" height="16"', 'width="10" height="10"');
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
      // parent 只来自启动记录；没有父记录的会话进“未归属”。terminal 表示用户在项目终端里自己启动、经批准当上主控的会话。
      agents: [
        { id: 'launch-41c7', age: '刚刚', project: 'inkwell', task: 'T-12', attempt: null, parent: null, role: 'controller', preset: 'ideation', terminal: true, cli: 'claude', state: 'waiting_user_answer' },
        { id: 'launch-8e02', age: '12 分', project: 'inkwell', task: 'T-12', attempt: null, parent: 'launch-41c7', role: 'controller', preset: 'executor', terminal: true, cli: 'claude', state: 'running' },
        { id: 'launch-a3f9', age: '4 分', project: 'inkwell', task: 'T-12', attempt: 'a2', parent: 'launch-8e02', role: 'worker', cli: 'codex', state: 'running' },
        { id: 'launch-c611', age: '4 分', project: 'inkwell', task: 'T-12', attempt: 'a2', parent: 'launch-8e02', role: 'monitor', cli: 'codex', state: 'idle' },
        { id: 'launch-2a6e', age: '2 小时', project: 'inkwell', task: 'T-11', attempt: 'a1', parent: 'launch-8e02', role: 'worker', cli: 'codex', state: 'idle' },
        { id: 'launch-5d20', age: '6 分', project: 'inkwell', task: 'T-11', attempt: 'a1', parent: 'launch-8e02', role: 'reviewer', cli: 'codex', state: 'running' },
        { id: 'launch-e7b4', age: '1 分', project: 'inkwell', task: 'T-14', attempt: 'a1', parent: 'launch-8e02', role: 'worker', cli: 'codex', state: 'waiting_controller_answer' },
        { id: 'launch-0b9d', age: '1 天', project: 'inkwell', task: 'T-09', attempt: 'a1', parent: 'launch-8e02', role: 'worker', cli: 'codex', state: 'ended' },
        { id: 'launch-62aa', age: '3 小时', project: 'tidepool', task: 'T-3', attempt: null, parent: null, role: 'controller', preset: 'ideation', terminal: true, cli: 'claude', state: 'running' },
        { id: 'launch-93fe', age: '3 小时', project: 'tidepool', task: 'T-3', attempt: null, parent: 'launch-62aa', role: 'controller', preset: 'executor', terminal: true, cli: 'claude', state: 'unrestored' },
        { id: 'launch-1d85', age: '3 小时', project: 'tidepool', task: 'T-3', attempt: 'a1', parent: 'launch-93fe', role: 'worker', cli: 'codex', state: 'unrestored' },
        { id: 'launch-f40c', age: '3 小时', project: 'tidepool', task: 'T-3', attempt: 'a1', parent: 'launch-93fe', role: 'reviewer', cli: 'codex', state: 'unknown' },
        ...['b1', 'b2', 'b3', 'b4', 'b5', 'b6'].map((suffix, index) => ({ id: 'launch-5e' + suffix, age: (20 + index * 7) + ' 分', project: 'tidepool', task: 'T-5', attempt: 'a1',
          parent: 'launch-93fe', role: 'worker', cli: 'codex', state: index === 2 ? 'idle' : 'running' })),
        { id: 'launch-7a31', age: '5 小时', project: 'tidepool', task: 'T-5', attempt: 'a1', parent: null, role: 'monitor', cli: 'codex', state: 'idle' },
        { id: 'launch-3b10', age: '25 分', project: 'ledger-cli', task: 'T-1', attempt: null, parent: null, role: 'controller', preset: 'ideation', terminal: true, cli: 'claude', state: 'idle' },
      ],
      // 项目终端里的 claude 经 `a2a request executor` 申请当执行主控，等你批准（renderer.tsx 的 role-requests）。
      roleRequests: [{ id: 'rr-1', project: 'ledger-cli', cli: 'claude', role: 'executor', role_label: '执行主控', opened: '10:42', cwd: '~/work/ledger-cli', pane: 'request' }],
      // 问题上报（IssuesPage.tsx）：只有 inkwell 有。
      issues: [
        { id: 'i-2', task: 'T-11', number: 2, title: '导入接口不校验未来时间戳', from: 'reviewer', blocking: true, state: '等你决定', created: '10/23 10:06',
          body: '审查 a81d3c0f52 时发现：导入文件里晚于当前时间的时间戳会原样写入，列表排序会被打乱。这不在 T-11 的范围里，要不要另开一张票？', answer: null, disposition: null },
        { id: 'i-1', task: 'T-12', number: 1, title: 'tests/export 有一个用例依赖本机时区', from: 'worker', blocking: false, state: '待判断', created: '10/23 09:58',
          body: 'test_export_dates 在 UTC 以外的时区会失败。它不是本票的验收文件，我没有改它。', answer: null, disposition: null },
        { id: 'i-0', task: 'T-09', number: 1, title: 'CSV 导出没有写 BOM', from: 'monitor', blocking: false, state: '已关闭', created: '10/22 16:20',
          body: 'Excel 打开含中文的导出文件会乱码。', answer: null, disposition: { action: 'close', reason: '旧版也不写 BOM，用户文档里已说明用“导入数据”打开' } },
      ],
      // 用户输入记录（RecordsPage.tsx）：你亲手打的字、答复和审批；主控发出的文字不算。
      records: [
        { time: '10/23 09:12:05', task: null, role: '构思主控', form: '消息', channel: '主控终端提交', text: '导出页想加个按标签筛选' },
        { time: '10/23 09:31:40', task: null, role: '项目终端', form: '批准', channel: '界面操作', text: '批准 inkwell 终端的 claude 成为执行主控' },
        { time: '10/23 09:44:12', task: 'T-11', role: 'worker', form: '消息', channel: '窗格键入', text: '时区统一按 UTC 存，别用本地时间', intervention: true },
        { time: '10/23 09:44:13', task: 'T-11', role: 'worker', form: '消息', channel: '窗格键入', text: '（按键：回车）', intervention: true },
        { time: '10/23 10:15:27', task: null, role: '构思主控', form: '消息', channel: '主控终端提交', text: 'T-12 先做，T-14 放到下周' },
      ],
      // 指标（MetricsPage.tsx）：与上面的任务和会话对得上。
      metrics: {
        byModel: [['claude-haiku-5-5', '项目级', 2, 41], ['gpt-6.1-sol', '前端界面', 1, 14], ['unknown', '前端界面', 1, 3], ['gpt-6.1-sol', '后端逻辑', 2, 29],
          ['gpt-6.1-sol', '重构', 1, 4], ['gpt-6.1-sol', '缺陷修复', 1, 9]],
        sessions: [['项目级', '构思主控', 'claude', 'claude-haiku-5-5', 'low', 26], ['项目级', '执行主控', 'claude', 'claude-haiku-5-5', 'low', 15],
          ['T-12', 'worker', 'codex', 'gpt-6.1-sol', 'high', 14], ['T-12', '监视器', 'codex', 'unknown', 'unknown', 3], ['T-11', 'worker', 'codex', 'gpt-6.1-sol', 'high', 21],
          ['T-11', '审查员', 'codex', 'gpt-6.1-sol', 'high', 8], ['T-14', 'worker', 'codex', 'gpt-6.1-sol', 'high', 4], ['T-09', 'worker', 'codex', 'gpt-6.1-sol', 'high', 9]],
        firstTime: { integrated: 1, firstTime: 0, rejections: [['路径边界', 1], ['完成条件', 1], ['独立审查', 1]] },
        attention: [['T-09', '缺陷修复', 1, 0, 1, 0]],
        scores: [['codex', 'gpt-6.1-sol', 'high', '缺陷修复', 1, '通过 1', 3, 2]],
      },
      // Reflect（ReflectPage.tsx）：历来启动过的主控和它们下面的会话，已结束的也在。
      reflect: [
        { id: 'r-old', parent: null, role: '构思主控', where: '项目终端', run: 'claude · claude-haiku-5-5 · low', time: '10/22 14:03 – 10/22 18:40', state: '已结束' },
        { id: 'r-41c7', parent: null, role: '构思主控', where: '项目终端', run: 'claude · claude-haiku-5-5 · low', time: '10/23 09:05', state: '运行中' },
        { id: 'r-8e02', parent: 'r-41c7', role: '执行主控', where: '项目终端', run: 'claude · claude-haiku-5-5 · low', time: '10/23 09:31', state: '运行中' },
        { id: 'r-0b9d', parent: 'r-8e02', role: 'worker', where: 'T-09', run: 'codex · gpt-6.1-sol · high', time: '10/22 15:10 – 10/22 16:52', state: '已结束',
          score: { result: '通过', boundary: [3, ''], taste: [2, '改动集中，但复制了一段转义逻辑'] } },
        { id: 'r-2a6e', parent: 'r-8e02', role: 'worker', where: 'T-11', run: 'codex · gpt-6.1-sol · high', time: '10/23 08:20', state: '运行中' },
        { id: 'r-5d20', parent: 'r-8e02', role: '审查员', where: 'T-11', run: 'codex · gpt-6.1-sol · high', time: '10/23 10:01', state: '运行中' },
        { id: 'r-a3f9', parent: 'r-8e02', role: 'worker', where: 'T-12', run: 'codex · gpt-6.1-sol · high', time: '10/23 10:11', state: '运行中' },
      ],
      // 复盘：默认每周一 09:00、Claude Code · claude-opus-5-5 · medium，开启前不跑（retrospective.ts）。
      retro: { enabled: false, weekday: 1, time: '09:00', runner: 'Claude Code · claude-opus-5-5 · medium', runs: [
          { start: '10/20 09:00', trigger: '手动', range: '最早 – 10/20 09:00', run: 'Claude Code · claude-opus-5-5 · medium', state: '已完成', report: 'findings/retrospective-2026-10-20.md' }],
        suggestions: [
          { id: 's-1', number: 1, title: '任务卡写明时区约定', kind: '写成 ticket', body: 'T-11 两次打回都和时区有关。建议在任务卡模板里加一栏“时间与时区约定”。', decision: null },
          { id: 's-2', number: 2, title: 'worker 角色卡提醒先跑完成条件', kind: '改角色卡', body: '两次交付里有一次没先跑完成条件就提交。', decision: null },
        ] },
      questions: [
        { id: 'q-1', launch: 'launch-41c7', target: 'user', cli: 'claude', status: 'waiting', question: '导出时，已归档的条目默认要不要包含在内？',
          options: [{ label: '不包含', description: '与列表页的默认筛选一致' }, { label: '包含', description: '导出更完整，但和列表页看到的不一样' }],
          replies: { '不包含': ['● 收到：默认不包含已归档条目。', '● 已写进 T-12 任务卡的目标，ready_rev 加 1，通知执行主控。'],
            '包含': ['● 收到：默认包含已归档条目，导出结果会和列表页不同。', '● 已写进 T-12 任务卡的目标，ready_rev 加 1，通知执行主控。'] },
          freeReply: ['● 收到你的答复，按上面这行原文继续。'] },
        { id: 'q-2', launch: 'launch-e7b4', target: 'controller', cli: 'codex', status: 'waiting', question: '旧版 0.8 的配置文件还需要能迁移吗？',
          options: [{ label: '不再支持', description: '删除迁移代码，在更新说明里写明' }, { label: '保留一个版本', description: '下个版本再删' }],
          replies: { '不再支持': ['› 按答复继续：删除 0.8 迁移代码，更新说明里写明。'],
            '保留一个版本': ['› 按答复继续：保留 0.8 迁移代码到下个版本，更新说明里写明下个版本删除。'] },
          freeReply: ['› 收到答复，按上面这行原文继续。'] },
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
      'launch-3b10': [['dim', '~/work/ledger-cli · claude'], ['', '> 先把命令行参数解析拆成一张票'], ['', '● 已写好 T-1 的任务卡，标记就绪'],
        ['', '● 这个项目还没有执行主控，T-1 暂时没人派发']],
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
        notifications: true, dockBadges: true, menu: null, renaming: null, zoom: null, settingsOpen: false, theme: 'system', execRole: 'worker', execDraft: null, execMessage: '',
        flowOpen: {}, flowExpanded: {}, drafts: {}, noticeSeen: new Set(), noticeActive: new Map(),
        issueDrafts: {}, closing: null, closeDraft: { reason: '', basis: '' }, parentChoice: 'launch-3b10', recordTask: '', recordSession: '', spot: null };
      panes = {}; layouts = {}; paneSeq = 0;
      const agentPane = launch => { const key = 'p' + (++paneSeq); panes[key] = { kind: 'agent', launch, lines: (lines[launch] || [['dim', '（演示没有为这个会话预设输出）']]).slice(), forward: false }; return key; };
      const shellPane = (cwd, label) => { const key = 'p' + (++paneSeq); panes[key] = { kind: 'shell', cwd, lines: shellLines(cwd), forward: false, project: label }; return key; };
      layouts['inkwell/T-12'] = { direction: 'right', first: agentPane('launch-41c7'), second: { direction: 'down', first: agentPane('launch-8e02'), second: agentPane('launch-a3f9') } };
      // 任务内分屏可以把普通终端放在 agent 旁（T-159）：它不算 worker，打字也不记人工介入。
      layouts['inkwell/T-11'] = { direction: 'right', first: agentPane('launch-2a6e'),
        second: { direction: 'down', first: agentPane('launch-5d20'), second: shellPane('~/work/inkwell', 'inkwell') } };
      layouts['inkwell/T-14'] = agentPane('launch-e7b4');
      layouts['inkwell/T-09'] = null;
      layouts['tidepool/T-3'] = { direction: 'down', first: { direction: 'right', first: agentPane('launch-62aa'), second: agentPane('launch-93fe') },
        second: { direction: 'right', first: agentPane('launch-1d85'), second: agentPane('launch-f40c') } };
      layouts['tidepool/T-5'] = null;
      layouts['ledger-cli/T-1'] = null;
      for (const project of data.projects) layouts[project.id] = null;
      // ledger-cli：左边是已批准的构思主控，右边是正在申请执行主控的项目终端。
      const requesting = shellPane('~/work/ledger-cli', 'ledger-cli');
      panes[requesting].lines = [['', '~/work/ledger-cli % claude'], ['', '> 你来当这个项目的执行主控'], ['', '● a2a request executor'],
        ['warn', '  已提交角色申请，等你在 Enchanted 里批准']];
      panes[requesting].request = 'rr-1';
      layouts['ledger-cli'] = { direction: 'right', first: agentPane('launch-3b10'), second: requesting };
      layouts.free = shellPane('~', null);
      root.removeAttribute('data-theme');
      ui.makeAgentPane = agentPane; ui.makeShellPane = shellPane;
    }

    const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
    const icon = state => `<span class="status-icon" data-glyph="${glyphs[state] ? state : 'unknown'}" aria-hidden="true">${svg(glyphs[state] || glyphs.unknown)}</span>`;
    const findProject = id => data.projects.find(project => project.id === id);
    const findTask = () => findProject(ui.project)?.tasks.find(task => task.id === ui.task) || null;
    const findAgent = id => data.agents.find(agent => agent.id === id);
    const layoutKey = () => ui.task ? `${ui.project}/${ui.task}` : ui.project ?? 'free';
    const roleLabel = agent => agent.role === 'controller' ? (agent.preset === 'ideation' ? '构思主控' : '执行主控')
      : { worker: 'worker', reviewer: '审查员', monitor: '监视器' }[agent.role];
    const paneRole = pane => {
      if (pane.kind === 'shell') return '普通终端';
      const agent = findAgent(pane.launch);
      return agent.role === 'controller' ? roleLabel(agent) : { worker: '受管 worker', reviewer: '独立审查', monitor: 'monitor' }[agent.role];
    };
    const issuesWaiting = project => project === 'inkwell' ? data.issues.filter(issue => issue.state === '等你决定').length : 0;
    const descendants = id =>data.agents.filter(child => child.parent === id).flatMap(child => [child, ...descendants(child.id)]);
    const openQuestions = launch => data.questions.filter(question => question.launch === launch && !['answered', 'cancelled'].includes(question.status));
    // 与 workbench/app/notificationCenter.ts 的 observe 相同：按问题记“已提醒过”，关闭期间看到的问题在重新开启后也不重放。
    const waitingQuestions = () => data.questions.filter(question => !['answered', 'cancelled'].includes(question.status)
      && findAgent(question.launch).state === 'waiting_user_answer');
    function notices() {
      const pending = new Map(waitingQuestions().map(question => [question.id, findAgent(question.launch)]));
      for (const id of [...ui.noticeActive.keys()]) if (!pending.has(id)) ui.noticeActive.delete(id);
      for (const [id, agent] of pending) {
        if (ui.notifications && !ui.noticeSeen.has(id)) ui.noticeActive.set(id, agent);
        ui.noticeSeen.add(id);
      }
      if (!ui.notifications) ui.noticeActive.clear();
      return [...ui.noticeActive.values()];
    }

    // ---------- 侧栏 ----------
    function agentBranches(rows, level, scope) {
      return `<ul class="agent-branches">${rows.map(agent => {
        const children = descendants(agent.id);
        const collapsed = ui.collapsed.has(agent.id);
        const summaryState = aggregate(children.map(child => child.state));
        const counts = Object.keys(stateLabels).filter(key => children.some(child => child.state === key))
          .map(key => `${stateLabels[key]} ${children.filter(child => child.state === key).length}`).join(' · ');
        const direct = scope.filter(child => child.parent === agent.id);
        const controllers = direct.filter(child => child.role === 'controller');
        const tasks = [...new Set(direct.filter(child => child.role !== 'controller').map(child => child.task))];
        return `<li><div class="agent-line" style="padding-left:${level * 14}px">
          ${children.length ? `<button class="agent-toggle" data-action="toggle-agent" data-agent-toggle="${agent.id}" data-fk="toggle:${agent.id}" aria-expanded="${!collapsed}"
            aria-controls="${root.id}-children-${agent.id}" aria-label="${collapsed ? '展开' : '折叠'}${roleLabel(agent)}的子会话">${chevron(collapsed)}</button>`
            : '<span class="agent-toggle-space" aria-hidden="true"></span>'}
          <button class="agent-row" data-action="agent" data-agent-launch="${agent.id}" data-agent-level="${level}" data-agent-state="${agent.state}" data-fk="agent:${agent.id}"
            title="${roleLabel(agent)} · ${esc(agent.task)} · ${agent.attempt ? 'attempt ' + agent.attempt : '无 attempt'} · ${agent.cli}"
            ${ui.focusedAgent === agent.id ? 'aria-current="true"' : ''} ${collapsed ? `data-descendant-state="${summaryState}"` : ''}>
            <span class="agent-main"><span class="agent-role">${roleLabel(agent)}</span><span class="agent-meta">${agent.terminal ? '项目终端' : esc(agent.task)} · ${agent.cli}</span>
              <span class="sr-only">${stateLabels[agent.state]}</span></span>
            <span class="row-time">${esc(agent.age)}</span>${icon(agent.state)}
            ${collapsed ? `<span class="agent-subtree" data-agent-summary="${agent.id}">子会话 ${children.length} · ${counts}</span>` : ''}
          </button></div>
          <div id="${root.id}-children-${agent.id}" ${collapsed ? 'hidden' : ''}>
            ${controllers.length ? agentBranches(controllers, level + 1, scope) : ''}
            ${tasks.map(task => `<div class="agent-task-group">${agentBranches(direct.filter(child => child.task === task && child.role !== 'controller'), level + 1, scope)}</div>`).join('')}
          </div></li>`;
      }).join('')}</ul>`;
    }
    function projectGroup(project) {
      const scope = data.agents.filter(agent => agent.project === project.id);
      const waiting = scope.filter(agent => agent.state === 'waiting_user_answer').length;
      const roots = scope.filter(agent => !agent.parent && agent.role === 'controller' && agent.preset === 'ideation');
      const orphans = scope.filter(agent => !agent.parent && !(agent.role === 'controller' && agent.preset === 'ideation'));
      // 与 renderer.tsx 的 projectGit 相同的写法。
      const git = `${project.git.branch}${project.git.upstream ? ` · ↑${project.git.ahead} ↓${project.git.behind}` : ' · 无上游'}`;
      const issues = issuesWaiting(project.id);
      return `<section class="project-group">
        <button class="project-row" data-action="project" data-project-id="${esc(project.id)}" data-fk="project:${esc(project.id)}"
          title="${esc(project.repo)}" ${ui.project === project.id ? 'aria-current="page"' : ''}>
          <span class="project-heading"><span class="project-title">${esc(project.id)}</span><span class="project-git">${esc(git)}</span></span>
          <span class="project-count">${scope.length || ''}</span>
          ${waiting ? `<span class="project-needs">${waiting} 个等你</span>` : ''}${issues ? `<span class="project-needs">${issues} 个问题</span>` : ''}</button>
        ${agentBranches(roots, 0, scope)}
        ${orphans.length ? `<div class="unassigned-agents">${roots.length ? '<div class="agent-task-label">未归属</div>' : ''}${agentBranches(orphans, 0, scope)}</div>` : ''}
      </section>`;
    }
    function sidebar() {
      return `<aside class="sidebar">
        <div class="sidebar-top"><span class="lights" aria-hidden="true"><i></i><i></i><i></i></span>
          <button class="icon-button" data-action="note" data-note="真实应用里这个按钮（⌘\\）隐藏或显示侧栏；演示里不隐藏。" data-fk="toggle-sidebar" aria-label="隐藏侧栏">${svgSidebar}</button>
          <button class="icon-button" data-action="settings-open" data-fk="settings" aria-label="设置">${svgGear}</button>
          <button class="icon-button" data-action="note" data-note="真实应用会弹出 macOS 的目录对话框：选一个目录，它就成了项目，之后在项目里新建的终端都从这个目录启动。演示里不打开对话框。" data-fk="create-project" aria-label="打开项目目录">${svgPlus}</button>
        </div>
        <nav class="project-list" aria-label="项目目录" data-sk="projects">${data.projects.map(projectGroup).join('')}
          <section class="project-group"><button class="project-row free-terminals" data-action="free" data-fk="free" ${!ui.project ? 'aria-current="page"' : ''}>
            <span class="project-title">独立终端</span><span class="project-count">家目录</span></button></section>
        </nav>
        <div class="sidebar-footer"><button class="text-button" data-action="note" data-note="演示数据是固定的，刷新不会变化。" data-fk="refresh">刷新列表</button></div>
      </aside>`;
    }

    // 设置（单独弹出）：外观、通知、主控派发的默认模型（ExecutionSettings.tsx）、状态图标。
    function settingsView() {
      if (!ui.settingsOpen) return '';
      const draft = ui.execDraft ?? data.execution[ui.execRole];
      return `<div class="settings-backdrop" data-action="settings-backdrop"><div class="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="${root.id}-settings-title">
        <header><h2 id="${root.id}-settings-title">设置</h2><button class="icon-button" data-action="settings-close" data-fk="settings-close" aria-label="关闭设置">${svgClose}</button></header>
        <section><h3>外观</h3><div class="segmented" role="group" aria-label="外观">${[['system', '跟随系统'], ['light', '浅色'], ['dark', '深色']].map(([value, label]) =>
          `<button data-action="theme" data-theme-value="${value}" data-fk="theme:${value}" aria-pressed="${ui.theme === value}">${label}</button>`).join('')}</div></section>
        <section><h3>通知</h3><fieldset class="notification-settings"><legend class="sr-only">应用内通知</legend>
          <label><input type="checkbox" data-setting="notifications" data-fk="setting:notifications" ${ui.notifications ? 'checked' : ''}>等待用户回答时提醒</label>
          <label><input type="checkbox" data-setting="dockBadges" data-fk="setting:dockBadges" ${ui.dockBadges ? 'checked' : ''}>后台时显示 Dock 待答数量</label></fieldset></section>
        <section><h3>主控派发的默认模型</h3>
          <p class="settings-note">主控派发新会话时按角色取这里的模型和思考强度，主控也可以按你在对话里的要求临时改。只影响之后启动的会话；已经打开的终端、正在运行的会话，以及你在终端里自己启动的 claude / codex 都不受影响。</p>
          <form class="execution-settings" aria-label="主控派发的默认模型" data-execution>
            <label>角色<select data-exec-role data-fk="exec:role">${Object.entries(executionLabels).map(([key, label]) =>
              `<option value="${key}" ${ui.execRole === key ? 'selected' : ''}>${label}</option>`).join('')}</select></label>
            <label>模型<input data-exec-field="model" data-fk="exec:model" required value="${esc(draft.model)}"></label>
            <label>思考强度<input data-exec-field="effort" data-fk="exec:effort" required value="${esc(draft.effort)}"></label>
            <label class="execution-fast"><input type="checkbox" data-exec-field="fast" data-fk="exec:fast" ${draft.fast ? 'checked' : ''}>Fast</label>
            <p>模型名和思考强度按 CLI 的写法填写，例如 gpt-6.1-sol 与 high。</p>
            <button data-fk="exec:save">保存</button>
            ${ui.execMessage ? `<p role="status">${esc(ui.execMessage)}</p>` : ''}
          </form></section>
        <section><h3>状态图标</h3><ul class="status-legend">${Object.entries(stateLabels).map(([state, label]) => `<li>${icon(state)}${label}</li>`).join('')}</ul></section>
      </div></div>`;
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
      const identity = shell ? pane.cwd
        : `${agent.role}${agent.preset ? '/' + agent.preset : ''} · task ${agent.task} · launch ${agent.id}${agent.attempt ? ' · attempt ' + agent.attempt : ''}`;
      const footer = shell ? '普通终端 · zsh' : agent.role === 'reviewer' ? '独立审查 · 只读' : agent.role === 'worker' ? '在此窗格输入会记录为人工介入' : '在此窗格输入会记录为用户输入';
      const lifecycle = shell ? '运行中' : agent.state === 'ended' ? '已结束' : agent.state === 'unknown' || agent.state === 'unrestored' ? '未知' : '运行中';
      return `<section class="pane${focused ? ' pane-focused' : ''}" data-pane-key="${key}" data-launch-id="${pane.launch ?? ''}" aria-label="${role}交互终端">
        ${!shell && restoreErrors[agent.id] ? `<div class="connection-error" role="alert">${esc(restoreErrors[agent.id])}</div>` : ''}
        <div class="pane-header"><strong title="${esc(name ?? role)}">${esc(name ?? role)}</strong>${name ? `<span class="pane-role">${role}</span>` : ''}
          <span class="pane-identity" title="${esc(identity)}">${esc(shell ? pane.cwd : identity)}</span>
          <span class="pane-badges"><span class="input-target">${focused && !readonly ? '正在输入' : ''}</span>
            ${readonly ? '<span class="readonly">只读</span>' : ''}${shell ? '' : `<span class="pane-state">${activity}</span>`}</span>
          <span class="pane-actions">
            <button class="icon-button pane-menu-trigger" data-action="menu" data-pane="${key}" data-fk="menu:${key}" aria-label="窗格菜单" aria-haspopup="menu" aria-expanded="${ui.menu?.pane === key}">${svgDots}</button>
            <button class="icon-button" data-action="close" data-pane="${key}" data-fk="close:${key}">${svgClose}<span class="sr-only">关闭窗格</span></button></span>
        </div>
        ${ui.renaming === key ? `<form class="pane-rename" data-rename="${key}"><label>窗格名称 <input data-rename-input="${key}" data-fk="rename:${key}" maxlength="100" value="${esc(ui.renameDraft)}"></label>
          <button data-fk="rename-save:${key}" ${ui.renameDraft.trim() ? '' : 'disabled'}>保存名称</button><button type="button" data-action="rename-cancel" data-fk="rename-cancel:${key}">取消</button></form>` : ''}
        <div class="questions-panel" aria-label="原生提问">${shell ? '' : openQuestions(agent.id).map(questionForm).join('')}</div>
        <div class="terminal-scroll" data-terminal="${key}" data-sk="term:${key}"><pre class="terminal-lines">${pane.lines.map(([kind, text]) =>
          kind ? `<span class="${kind}">${esc(text)}</span>` : esc(text)).join('\n')}</pre></div>
        ${shell ? '' : `<div class="pane-footer"><span>${footer}</span><span>执行：${lifecycle}</span></div>`}
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
        ${project ? `<nav class="task-strip" aria-label="项目任务" data-sk="tasks">
          ${project.tasks.map(item => `<button class="task-row" data-action="task" data-task-option="${item.id}" data-fk="task:${item.id}" ${task && task.id === item.id ? 'aria-current="page"' : ''}>
            <span class="task-title">${esc(item.title)}</span><span class="task-meta">${item.id} · ${gateNames[item.state]}</span></button>`).join('')}</nav>` : ''}
        ${roleRequestsView()}
        <div class="pane-layout" aria-label="终端窗格">
          ${keys.map(key => {
            const rect = ui.zoom === key ? { x: 0, y: 0, w: 100, h: 100 } : rects[key];
            const request = data.roleRequests.find(item => item.id === panes[key].request && !item.decided);
            return `<div class="pane-slot" ${request ? 'data-role-request-pending="true"' : ''} data-edge-right="${rect.x + rect.w >= 99.9}" data-edge-bottom="${rect.y + rect.h >= 99.9}" ${ui.zoom && ui.zoom !== key ? 'hidden' : ''} style="left:${rect.x}%;top:${rect.y}%;width:${rect.w}%;height:${rect.h}%">${request ? `<span class="role-request-tag">申请 1 · ${request.role_label}</span>` : ''}${paneView(key, ui.focusedPane === key)}</div>`;
          }).join('')}
          ${/* 真实应用按 agent.task 计数，主控的 task 恒为 null；演示数据给主控挂了 T-12，所以这里显式排除主控。 */''}
          ${!keys.length && !task && project?.tasks.length ? `<div class="project-task-grid" aria-label="项目任务分屏">
            ${project.tasks.map(item => `<button class="project-task-tile" data-action="task" data-task-option="${item.id}" data-task-tile="${item.id}" data-fk="tile:${item.id}">
              <span class="task-meta">${gateNames[item.state]}</span><strong>${esc(item.title)}</strong><span class="task-meta">${item.id}</span>
              <span class="task-agents">${data.agents.filter(agent => agent.project === project.id && agent.task === item.id && agent.role !== 'controller').length} 个 agent<span aria-hidden="true"> ↗</span></span></button>`).join('')}
          </div>` : ''}
          ${keys.length || !task && project?.tasks.length ? '' : `<div class="selection-hint"><h2>${task ? '这个任务还没有打开的窗格' : project ? '还没有打开的终端' : '独立终端'}</h2>
            <p>${project ? `新建的终端从 ${esc(project.repo)} 启动。经门禁派发的会话会按项目出现在左边。` : '这里的终端从家目录启动，不属于任何项目。'}</p>
            <button class="primary-button" data-action="new-terminal" data-fk="hint-new-terminal">新建终端</button></div>`}
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
            <small>${icon(agent.state)} ${stateLabels[agent.state]}</small></span></div>`).join('')}
        ${list.length > 4 ? `<button class="flow-more" data-action="flow-more" data-group="${group}" data-flow-more="${group}" data-fk="more:${group}" aria-expanded="${Boolean(expanded)}">${expanded ? '收起' : `还有 ${list.length - 4} 个 ↗`}</button>` : ''}
      </div>`;
    }
    function flowPage() {
      const lanes = data.projects.flatMap(project => project.tasks.map(task => ({ project: project.id, task })));
      const live = agent => agent.state !== 'ended';
      const unassigned = data.agents.filter(agent => !agent.parent && !(agent.role === 'controller' && agent.preset === 'ideation') && live(agent));
      return `<section class="flow-page" aria-label="系统流程" data-sk="flow-page">
        <div class="flow-intro"><h2>系统流程</h2><p>一张票一条泳道 · 阶段来自门禁记录 · agent 只按已保存的归属展示</p>
          <p class="flow-legend">${Object.entries(stateLabels).map(([state, label]) => `<span>${icon(state)}${label}</span>`).join('')}</p></div>
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

    // ---------- 角色申请（renderer.tsx 的 role-requests） ----------
    function roleRequestsView() {
      const pending = data.roleRequests.filter(request => !request.decided);
      if (!pending.length) return '';
      return `<div class="role-requests" aria-label="角色申请" data-sk="role-requests">${pending.map((request, index) => {
        const here = ui.project === request.project;
        const ideations = data.agents.filter(agent => agent.project === request.project && agent.role === 'controller' && agent.preset === 'ideation' && agent.state !== 'ended');
        return `<div class="role-request" data-role-request="${request.id}" role="alert">
          <span class="role-request-number" aria-label="申请 ${index + 1}">${index + 1}</span>
          <p><strong>${esc(request.project)}</strong> 的${here ? '右侧窗格' : `${request.opened} 打开的终端（${esc(request.cwd)}）`}里的 ${request.cli} 申请成为<strong>${request.role_label}</strong>${here ? '' : '<span class="role-request-hint">，不在当前视图</span>'}</p>
          ${ideations.length ? `<label class="role-request-parent">上级<select data-role-parent data-fk="rr-parent">${ideations.map(agent =>
            `<option value="${agent.id}" ${ui.parentChoice === agent.id ? 'selected' : ''}>构思主控 · 项目终端 · ${agent.cli}</option>`).join('')}
            <option value="" ${ui.parentChoice === '' ? 'selected' : ''}>不归属</option></select></label>` : ''}
          <button class="text-button" data-action="rr-decide" data-request="${request.id}" data-approve="false" data-fk="rr-deny">拒绝</button>
          <button class="primary-button" data-action="rr-decide" data-request="${request.id}" data-approve="true" data-fk="rr-approve">批准</button>
        </div>`;
      }).join('')}</div>`;
    }

    // ---------- 问题、记录、指标、Reflect ----------
    const emptyProject = () => `<p class="records-empty">先在左侧选一个项目。</p>`;
    const roleNames = { worker: 'worker', reviewer: '审查员', monitor: '监视器' };
    const dispositionNames = { close: '已关闭', snooze: '稍后再看' };
    function issuesPage() {
      const rows = ui.project === 'inkwell' ? [...data.issues].sort((a, b) => Number(b.state !== '已关闭') - Number(a.state !== '已关闭')) : [];
      return `<div class="records-page issues-page" data-sk="page:issues">
        <div class="records-intro"><h2>问题上报</h2>
          <p>worker、审查员和监视器发现任务范围外的问题时报到这里。答复会写进上报它的会话；标了“阻塞”的只有你能关闭。关闭的问题保留记录。</p></div>
        ${!ui.project ? emptyProject() : !rows.length ? '<p class="records-empty">这个项目还没有问题上报。</p>' : ''}
        ${rows.map(issue => {
          const settled = issue.state === '已关闭';
          const draft = ui.issueDrafts[issue.id] ?? '';
          return `<article class="record-card issue-card" data-issue-id="${issue.id}" data-issue-state="${issue.state}">
            <header class="record-heading"><strong>${issue.task} · 问题 ${issue.number}：${esc(issue.title)}</strong>
              <span class="record-state" ${issue.state === '等你决定' ? 'data-tone="needs"' : settled ? 'data-tone="quiet"' : ''}>${issue.state}</span>
              ${issue.blocking ? '<span class="record-badge">阻塞</span>' : ''}</header>
            <p class="record-meta">${roleNames[issue.from]} 上报 · ${issue.created}</p>
            <p class="record-body">${esc(issue.body)}</p>
            ${issue.answer ? `<p class="record-reply"><span>答复</span>${esc(issue.answer)}</p>` : ''}
            ${issue.disposition ? `<p class="record-reply"><span>处置</span>${dispositionNames[issue.disposition.action]}${issue.disposition.reason ? '：' + esc(issue.disposition.reason) : ''}</p>` : ''}
            ${!settled && !issue.answer ? `<form class="record-actions" data-issue-form="${issue.id}">
              <label>答复<textarea rows="2" maxlength="4000" data-issue-answer="${issue.id}" data-fk="issue-answer:${issue.id}">${esc(draft)}</textarea></label>
              <div class="record-buttons"><button class="primary-button" data-fk="issue-send:${issue.id}" ${draft.trim() ? '' : 'disabled'}>发送答复</button>
                <button type="button" class="text-button" data-action="issue-snooze" data-issue="${issue.id}" data-fk="issue-snooze:${issue.id}">稍后再看</button>
                <button type="button" class="text-button" data-action="issue-closing" data-issue="${issue.id}" data-fk="issue-closing:${issue.id}" aria-expanded="${ui.closing === issue.id}">关闭…</button></div>
            </form>` : ''}
            ${ui.closing === issue.id ? `<form class="record-actions" data-issue-close="${issue.id}">
              <label>为什么关闭<input maxlength="1000" data-close-field="reason" data-fk="close-reason" value="${esc(ui.closeDraft.reason)}"></label>
              <label>依据（看了什么）<input maxlength="1000" data-close-field="basis" data-fk="close-basis" value="${esc(ui.closeDraft.basis)}"></label>
              <div class="record-buttons"><button class="primary-button" data-fk="close-confirm" ${ui.closeDraft.reason.trim() && ui.closeDraft.basis.trim() ? '' : 'disabled'}>确认关闭</button></div>
            </form>` : ''}
          </article>`;
        }).join('')}
      </div>`;
    }

    function recordsPage() {
      const all = ui.project === 'inkwell' ? data.records : [];
      const tasks = [...new Set(all.map(record => record.task ?? ''))];
      const sessions = [...new Set(all.filter(record => !ui.recordTask || (record.task ?? '') === ui.recordTask).map(record => record.role + ' · ' + (record.task ?? '项目级')))];
      const rows = all.filter(record => (!ui.recordTask || (record.task ?? '') === ui.recordTask) && (!ui.recordSession || record.role + ' · ' + (record.task ?? '项目级') === ui.recordSession));
      return `<div class="records-page user-input-page" data-sk="page:records">
        <div class="records-intro"><h2>用户输入记录</h2>
          <p>你亲手打的字、在面板里的答复和审批都记在这里，主控和后台派发的文字不算。项目终端里只记你批准为主控的 Claude Code 或 Codex 收到的整条提示词，以及你对它提问的答复。落在受管 worker 会话里的输入记为人工介入。</p></div>
        ${!ui.project ? emptyProject() : !all.length ? '<p class="records-empty">这个项目还没有用户输入记录。</p>' : `
        <div class="record-filter"><label>任务 <select data-record-task data-fk="record-task"><option value="">全部</option>${tasks.map(task =>
          `<option value="${task}" ${ui.recordTask === task ? 'selected' : ''}>${task || '项目级'}</option>`).join('')}</select></label>
          <label>会话 <select data-record-session data-fk="record-session"><option value="">全部</option>${sessions.map(session =>
            `<option ${ui.recordSession === session ? 'selected' : ''}>${session}</option>`).join('')}</select></label>
          <span class="record-meta">${rows.length} 条，其中人工介入 ${rows.filter(record => record.intervention).length} 条</span></div>
        <table class="record-table"><thead><tr><th>时间</th><th>任务</th><th>会话</th><th>形态</th><th>来源</th><th>内容</th></tr></thead>
          <tbody>${rows.map(record => `<tr ${record.intervention ? 'data-intervention="true"' : ''}><td>${record.time}</td><td>${record.task ?? '项目级'}</td><td>${record.role}</td>
            <td>${record.form}${record.intervention ? '<span class="record-badge record-intervention">人工介入</span>' : ''}</td><td>${record.channel}</td>
            <td class="record-text">${esc(record.text)}</td></tr>`).join('')}</tbody></table>`}
      </div>`;
    }

    const table = (head, rows) => `<table class="record-table"><thead><tr>${head.map(cell => `<th>${cell}</th>`).join('')}</tr></thead>
      <tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${esc(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
    function metricsPage() {
      const metrics = data.metrics, mine = ui.project === 'inkwell';
      const none = '<span class="metric-none">无数据</span>';
      const rate = metrics.firstTime.integrated ? Math.round(metrics.firstTime.firstTime / metrics.firstTime.integrated * 1000) / 10 : null;
      return `<div class="records-page metrics-page" data-sk="page:metrics">
        <div class="records-intro"><h2>指标</h2>
          <p>每次打开都从记录现算，不另存计数。模型取会话里实际观察到的值；看不到的记为 unknown，单独成行。看板上的变化只算观察，不能当成改进的证明。</p></div>
        ${!ui.project ? emptyProject() : `
        <div class="record-filter"><label>从 <input type="date" data-fk="metrics-since"></label><label>到 <input type="date" data-fk="metrics-until"></label></div>
        <section class="metric-section" data-metric="model-use"><h3>模型使用</h3>
          ${mine ? table(['模型', '任务类型', '会话数', '回合数'], metrics.byModel) + table(['任务', '角色', 'CLI', '模型', '强度', '回合数'], metrics.sessions) : none}</section>
        <section class="metric-section" data-metric="first-time"><h3>一次到位率</h3>
          <p class="record-body">第一次交付就过完整门禁、全程没人介入，才算一次到位。</p>
          ${mine && rate !== null ? `<p class="metric-figure">${rate}%<span class="record-meta">（集成 ${metrics.firstTime.integrated} 个，一次到位 ${metrics.firstTime.firstTime} 个）</span></p>` : none}
          <h4>打回原因</h4>${mine ? table(['检查项', '打回次数'], metrics.firstTime.rejections) : none}</section>
        <section class="metric-section" data-metric="attention"><h3>你的注意力消耗</h3>
          <p class="record-body">每个集成的任务一行，数的是这个任务全部 attempt 的累计。</p>
          ${mine ? table(['集成的任务', '任务类型', '答题', '审批', '介入', '叫停'], metrics.attention) : none}</section>
        <section class="metric-section" data-metric="scores"><h3>打分汇总</h3>
          ${mine ? table(['CLI', '模型', '强度', '任务类型', 'attempt 数', '结果', '边界纪律', '工程品味'], metrics.scores) : none}</section>`}
      </div>`;
    }

    function reflectBranch(nodes, level) {
      return `<ul class="reflect-branch">${nodes.map(node => {
        const children = data.reflect.filter(child => child.parent === node.id);
        return `<li><div class="reflect-node" data-reflect-node="${node.id}" style="padding-left:${level * 18}px">
          <div class="reflect-line"><strong>${node.role}</strong><span class="record-meta">${node.where}</span><span class="record-meta">${node.run}</span>
            <span class="record-meta">${node.time}</span><span class="record-state" data-tone="${node.state === '运行中' ? 'needs' : 'quiet'}">${node.state}</span></div>
          ${node.score ? `<dl class="reflect-score"><div><dt>结果</dt><dd>${node.score.result}</dd></div>
            <div><dt>边界纪律</dt><dd>${node.score.boundary[0]}${node.score.boundary[1] ? `（${esc(node.score.boundary[1])}）` : ''}</dd></div>
            <div><dt>工程品味</dt><dd>${node.score.taste[0]}${node.score.taste[1] ? `（${esc(node.score.taste[1])}）` : ''}</dd></div></dl>` : ''}
        </div>${children.length ? reflectBranch(children, level + 1) : ''}</li>`;
      }).join('')}</ul>`;
    }
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    function reflectPage() {
      if (!ui.project) return `<div class="records-page reflect-page">${emptyProject()}</div>`;
      const mine = ui.project === 'inkwell', retro = data.retro;
      return `<div class="records-page reflect-page" data-sk="page:reflect">
        <div class="records-intro"><h2>Reflect</h2>
          <p>这个项目历来启动过的主控，和它们下面启动的执行主控、worker、审查员、监视器，已结束的也在。worker 上是主控给它那次交付的打分。</p></div>
        <section class="metric-section reflect-tree"><h3>主控与会话</h3>
          ${mine ? reflectBranch(data.reflect.filter(node => !node.parent), 0) : '<p class="metric-none">演示只为 inkwell 准备了会话树。</p>'}</section>
        <div class="retrospective-page"><div class="records-intro"><h2>复盘</h2>
          <p>复盘会话在一个普通项目终端里跑，只读代码和记录，只写自己的报告。报告存到项目的 findings/（没有这个目录就存在工作台数据目录）；改进建议列在下面，批准的先只记在这里。</p></div>
          <section class="metric-section"><h3>立即复盘</h3>
            <div class="record-filter"><label>CLI <select data-fk="retro-cli"><option>Claude Code</option><option>Codex</option></select></label>
              <label>模型 <input value="claude-opus-5-5" data-fk="retro-model"></label><label>思考强度 <input value="medium" size="8" data-fk="retro-effort"></label>
              <button class="primary-button" data-action="note" data-note="真实应用会在一个项目终端里启动复盘会话；演示不启动。" data-fk="retro-start">立即复盘</button></div>
            <p class="record-meta">时间范围从这个项目上次复盘到现在。</p></section>
          <section class="metric-section"><h3>定期复盘</h3>
            <div class="record-filter"><label><input type="checkbox" data-retro-enabled data-fk="retro-enabled" ${retro.enabled ? 'checked' : ''}>开启</label>
              <label>每 <select data-fk="retro-weekday">${weekdays.map((name, index) => `<option ${index === retro.weekday ? 'selected' : ''}>${name}</option>`).join('')}</select></label>
              <label><input type="time" value="${retro.time}" data-fk="retro-time"></label></div>
            <div class="record-filter"><label>由 <select data-fk="retro-runner-cli"><option>Claude Code</option><option>Codex</option></select></label>
              <label>模型 <input value="claude-opus-5-5" data-fk="retro-runner-model"></label><label>思考强度 <input value="medium" size="8" data-fk="retro-runner-effort"></label>
              <button class="text-button" data-action="note" data-note="真实应用会保存定期复盘用的 CLI、模型和思考强度；演示不保存。" data-fk="retro-runner-save">保存</button>
              <span class="record-meta">现在用 ${retro.runner}${retro.enabled ? '' : '（未开启）'}</span></div></section>
          <section class="metric-section"><h3>改进建议</h3>
            ${mine ? retro.suggestions.map(item => `<article class="record-card suggestion-card" data-suggestion-id="${item.id}">
              <header class="record-heading"><strong>${item.number}. ${esc(item.title)}</strong>
                <span class="record-state" data-tone="${item.decision ? 'quiet' : 'needs'}">${item.decision ? (item.decision.approved ? '已批准' : '不采纳') : '等你决定'}</span>
                <span class="record-meta">${item.kind}</span></header>
              <p class="record-body">${esc(item.body)}</p>
              ${item.decision ? '' : `<div class="record-buttons"><button class="primary-button" data-action="suggestion" data-suggestion="${item.id}" data-approve="true" data-fk="sg-yes:${item.id}">批准</button>
                <button class="text-button" data-action="suggestion" data-suggestion="${item.id}" data-approve="false" data-fk="sg-no:${item.id}">不采纳</button></div>`}
            </article>`).join('') : '<p class="metric-none">还没有建议。</p>'}</section>
          <section class="metric-section"><h3>复盘记录</h3>
            ${mine ? table(['开始', '方式', '范围', '执行', '状态', '报告'], retro.runs.map(run => [run.start, run.trigger, run.range, run.run, run.state, run.report]))
              : '<p class="metric-none">还没有复盘。</p>'}</section>
        </div>
      </div>`;
    }

    // ---------- 整体渲染 ----------
    function render() {
      const active = document.activeElement && root.contains(document.activeElement) ? document.activeElement.getAttribute('data-fk') : null;
      const scrolls = {};
      root.querySelectorAll('[data-sk]').forEach(el => { scrolls[el.dataset.sk] = [el.scrollTop, el.scrollLeft]; });
      const pending = notices();
      const waiting = waitingQuestions().length;
      const task = findTask();
      const project = findProject(ui.project);
      root.innerHTML = `${sidebar()}
          <main>
            <header class="task-header"><div class="header-title"><h1>${task ? esc(task.title) : project ? esc(project.id) : '独立终端'}</h1>
              <span class="eyebrow">${task ? `${esc(ui.project)} / ${esc(task.id)}` : project ? esc(project.repo) : '~'}</span></div>
              <nav class="workspace-pages" aria-label="工作区页面">
                <button data-action="page" data-page="terminal" data-fk="page:terminal" ${ui.page === 'terminal' ? 'aria-current="page"' : ''}>终端</button>
                <button data-action="page" data-page="flow" data-flow-tab data-fk="page:flow" ${ui.page === 'flow' ? 'aria-current="page"' : ''}>流程</button>
                <button data-action="page" data-page="issues" data-fk="page:issues" ${ui.page === 'issues' ? 'aria-current="page"' : ''}>问题${issuesWaiting(ui.project) ? `<span class="tab-needs" aria-label="${issuesWaiting(ui.project)} 个等你决定">${issuesWaiting(ui.project)}</span>` : ''}</button>
                <button data-action="page" data-page="records" data-fk="page:records" ${ui.page === 'records' ? 'aria-current="page"' : ''}>记录</button>
                <button data-action="page" data-page="metrics" data-fk="page:metrics" ${ui.page === 'metrics' ? 'aria-current="page"' : ''}>指标</button>
                <button data-action="page" data-page="reflect" data-fk="page:reflect" ${ui.page === 'reflect' ? 'aria-current="page"' : ''}>Reflect</button>
              </nav>
              <span class="connection">演示数据<output data-dock aria-label="Dock 角标">${ui.dockBadges && waiting ? `<span class="dock-badge" title="Dock 角标">${waiting}</span>` : ''}</output></span>
              <button class="primary-button" data-action="new-terminal" data-fk="new-terminal">新建终端</button></header>
            ${{ flow: flowPage, issues: issuesPage, records: recordsPage, metrics: metricsPage, reflect: reflectPage }[ui.page]?.() ?? ''}
            ${terminalPage()}
          </main>
        <aside class="app-notifications" aria-label="待回答通知" aria-live="polite">${pending.map(agent => `<button data-action="notice" data-notice-launch="${agent.id}" data-fk="notice:${agent.id}">
          <strong>等待用户回答</strong><span>${agent.project} · ${roleLabel(agent)}</span><span>${agent.task ?? '未归属任务'} · 查看问题 →</span></button>`).join('')}</aside>
        ${menuView()}${settingsView()}
        <p class="wb-note" role="status" data-note-out>${esc(ui.note ?? '')}</p>`;
      root.querySelectorAll('[data-sk]').forEach(el => { const saved = scrolls[el.dataset.sk]; if (saved) { el.scrollTop = saved[0]; el.scrollLeft = saved[1]; } });
      if (ui.menu) root.querySelector('.pane-menu button')?.focus({ preventScroll: true });
      else if (ui.settingsFresh) { root.querySelector('.segmented [aria-pressed="true"]')?.focus({ preventScroll: true }); ui.settingsFresh = false; }
      else if (ui.renaming && ui.renameFresh) { const input = root.querySelector('[data-rename-input]'); input?.focus({ preventScroll: true }); input?.select(); ui.renameFresh = false; }
      else if (ui.focusTarget) { root.querySelector(`[data-fk="${ui.focusTarget}"]`)?.focus({ preventScroll: true }); ui.focusTarget = null; }
      else if (active) root.querySelector(`[data-fk="${CSS.escape(active)}"]`)?.focus({ preventScroll: true });
      // 导览高亮当前这一步讲到的区域；找不到就不高亮。
      if (ui.spot) root.querySelectorAll(ui.spot).forEach(el => el.classList.add('wb-spot'));
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
      // 导览把窗口整体缩放显示；菜单坐标换回窗口自身的像素。
      const box = root.getBoundingClientRect(), scale = box.width / root.offsetWidth || 1;
      const x = (clientX - box.left) / scale, y = (clientY - box.top) / scale;
      ui.menu = { pane, x: Math.max(4, Math.min(x, root.offsetWidth - 218)), y: Math.max(4, Math.min(y, root.offsetHeight - 280)) };
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
    // 你在演示里的答复、审批也记进“记录”页，和真实应用一样只记你亲手做的。
    function record(task, role, form, channel, text) {
      const now = new Date(), pad = value => String(value).padStart(2, '0');
      data.records.push({ time: `${now.getMonth() + 1}/${now.getDate()} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`, task, role, form, channel, text });
    }
    function decideRoleRequest(id, approve) {
      const request = data.roleRequests.find(item => item.id === id);
      request.decided = true;
      const pane = Object.values(panes).find(item => item.request === id);
      if (approve) {
        const agent = { id: 'launch-c4e8', age: '刚刚', project: request.project, task: 'T-1', attempt: null, parent: ui.parentChoice || null, role: 'controller',
          preset: 'executor', terminal: true, cli: request.cli, state: 'running' };
        data.agents.push(agent);
        if (pane) { pane.kind = 'agent'; pane.launch = agent.id; pane.lines.push(['ok', '  已批准：本终端现在是 ledger-cli 的执行主控'], ['', '› 读取就绪的 T-1，准备派发 worker']); }
        ui.note = ui.parentChoice ? '已批准。执行主控出现在侧栏的构思主控下面。' : '已批准。执行主控没有上级，出现在侧栏的“未归属”里。';
      } else {
        if (pane) pane.lines.push(['dim', '  申请被拒绝']);
        ui.note = '已拒绝。这个终端还是普通终端，不能用主控命令。';
      }
      if (request.project === 'inkwell') record(null, '项目终端', approve ? '批准' : '拒绝', '界面操作', `${approve ? '批准' : '拒绝'} ${request.project} 终端的 ${request.cli} 成为${request.role_label}`);
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
        // 只有对象自身的预设选项键才算命中：constructor、__proto__ 之类的文本是普通自由答复，不能取到原型成员。
        // 自由答复只确认收到原文，不套用任何预设决定。
        const reply = Object.hasOwn(question.replies, value) ? question.replies[value] : question.freeReply;
        if (paneKey && panes[paneKey]) panes[paneKey].lines.push(['info', '› ' + value], ...reply.map(text => ['', text]));
        if (agent.project === 'inkwell') record(agent.terminal ? null : agent.task, roleLabel(agent), '答复', '界面操作', value);
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
          Object.assign(ui, { project: project.id, task: null, focusedAgent: null, focusedPane: null, page: 'terminal', zoom: null, menu: null });
          break;
        }
        case 'task': Object.assign(ui, { task: target.dataset.taskOption, focusedPane: null, focusedAgent: null, zoom: null, menu: null }); break;
        case 'free': Object.assign(ui, { project: null, task: null, focusedAgent: null, focusedPane: null, page: 'terminal', zoom: null, menu: null }); break;
        case 'settings-open': ui.settingsOpen = true; ui.settingsFresh = true; ui.menu = null; break;
        case 'settings-close': ui.settingsOpen = false; ui.focusTarget = 'settings'; break;
        case 'settings-backdrop': if (event.target !== target) return; ui.settingsOpen = false; ui.focusTarget = 'settings'; break;
        case 'theme': ui.theme = target.dataset.themeValue; if (ui.theme === 'system') root.removeAttribute('data-theme'); else root.dataset.theme = ui.theme; break;
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
          const next = ui.makeShellPane(panes[paneKey].cwd ?? (ui.project ? findProject(ui.project).repo : '~'), ui.project);
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
          // 项目里新建的终端从项目目录启动，独立终端从家目录启动。
          const next = ui.makeShellPane(ui.project ? findProject(ui.project).repo : '~', ui.project);
          const layoutId = layoutKey();
          layouts[layoutId] = layouts[layoutId] ? { direction: 'right', first: layouts[layoutId], second: next } : next;
          ui.zoom = null;
          break;
        }
        case 'option': ui.drafts[target.dataset.question] = target.dataset.option; break;
        case 'flow-toggle': ui.flowOpen[target.dataset.task] = target.getAttribute('aria-expanded') !== 'true'; break;
        case 'flow-more': ui.flowExpanded[target.dataset.group] = !ui.flowExpanded[target.dataset.group]; break;
        case 'note': ui.note = target.dataset.note; break;
        case 'rr-decide': decideRoleRequest(target.dataset.request, target.dataset.approve === 'true'); break;
        case 'issue-snooze': {
          const issue = data.issues.find(item => item.id === target.dataset.issue);
          issue.state = '稍后'; issue.disposition = { action: 'snooze' }; ui.closing = null;
          break;
        }
        case 'issue-closing': ui.closing = ui.closing === target.dataset.issue ? null : target.dataset.issue; ui.closeDraft = { reason: '', basis: '' }; break;
        case 'suggestion': {
          const item = data.retro.suggestions.find(entry => entry.id === target.dataset.suggestion);
          item.decision = { approved: target.dataset.approve === 'true' };
          ui.note = item.decision.approved ? '已批准。建议先只记在这里，不会自动改文件，也不送给构思主控。' : '已标为不采纳。';
          break;
        }
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
      else if (form.dataset.issueForm) {
        const issue = data.issues.find(item => item.id === form.dataset.issueForm);
        const value = (ui.issueDrafts[issue.id] ?? '').trim();
        if (!value) return;
        issue.answer = value; issue.state = '已答复'; ui.closing = null;
        record(issue.task, roleNames[issue.from], '答复', '问题面板', value);
        ui.note = `答复已写进上报它的${roleNames[issue.from]}会话。`; render();
      }
      else if (form.dataset.issueClose) {
        const issue = data.issues.find(item => item.id === form.dataset.issueClose);
        if (!ui.closeDraft.reason.trim() || !ui.closeDraft.basis.trim()) return;
        issue.state = '已关闭'; issue.disposition = { action: 'close', reason: ui.closeDraft.reason.trim() }; ui.closing = null;
        record(issue.task, roleNames[issue.from], '操作', '问题面板', '关闭问题：' + ui.closeDraft.reason.trim()); render();
      }
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
      } else if (el.dataset.issueAnswer) {
        ui.issueDrafts[el.dataset.issueAnswer] = el.value;
        el.closest('form').querySelector('.primary-button').disabled = !el.value.trim();
      } else if (el.dataset.closeField) {
        ui.closeDraft[el.dataset.closeField] = el.value;
        el.closest('form').querySelector('.primary-button').disabled = !(ui.closeDraft.reason.trim() && ui.closeDraft.basis.trim());
      } else if (el.dataset.execField && el.type !== 'checkbox') {
        ui.execDraft = { ...(ui.execDraft ?? data.execution[ui.execRole]), [el.dataset.execField]: el.value };
      } else if (el.dataset.renameInput) {
        ui.renameDraft = el.value;
        el.closest('form').querySelector('button:not([type])').disabled = !el.value.trim();
      }
    });

    root.addEventListener('change', event => {
      const el = event.target;
      if (el.dataset.setting) {
        ui[el.dataset.setting] = el.checked;
        if (el.dataset.setting === 'notifications' && !el.checked) ui.noticeActive.clear();
        render();
      }
      else if (el.hasAttribute('data-role-parent')) ui.parentChoice = el.value;
      else if (el.hasAttribute('data-record-task')) { ui.recordTask = el.value; ui.recordSession = ''; render(); }
      else if (el.hasAttribute('data-record-session')) { ui.recordSession = el.value; render(); }
      else if (el.hasAttribute('data-retro-enabled')) {
        data.retro.enabled = el.checked;
        ui.note = el.checked ? '已开启：每周一 09:00 自动复盘。' : '已关闭定期复盘。'; render();
      }
      else if (el.hasAttribute('data-exec-role')) { ui.execRole = el.value; ui.execDraft = null; ui.execMessage = ''; render(); }
      else if (el.dataset.execField === 'fast') ui.execDraft = { ...(ui.execDraft ?? data.execution[ui.execRole]), fast: el.checked };
    });

    root.addEventListener('keydown', event => {
      if (ui.menu && event.target.closest('.pane-menu')) {
        const items = [...root.querySelectorAll('.pane-menu button')];
        const index = items.indexOf(document.activeElement);
        if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
          event.preventDefault();
          items[event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus({ preventScroll: true });
        } else if (event.key === 'Escape' || event.key === 'Tab') { event.preventDefault(); closeMenu(); render(); }
      } else if (event.key === 'Tab' && ui.settingsOpen) {
        const items = [...root.querySelectorAll('.settings-dialog button, .settings-dialog input, .settings-dialog select')].filter(el => !el.disabled);
        const first = items[0], last = items[items.length - 1];
        if (!document.activeElement.closest('.settings-dialog')) { event.preventDefault(); (event.shiftKey ? last : first).focus(); }
        else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      } else if (event.key === 'Escape' && ui.settingsOpen) {
        ui.settingsOpen = false; ui.focusTarget = 'settings'; render();
      } else if (event.key === 'Escape' && event.target.dataset.renameInput) {
        ui.focusTarget = 'menu:' + ui.renaming; ui.renaming = null; render();
      }
    });

    // 页面导览的场景：只切换视图和高亮，不清掉你在演示里做过的操作；reset 才回到初始数据。
    const scenes = {
      sidebar: { project: 'inkwell', task: 'T-12', page: 'terminal', spot: '.project-list' },
      role: { project: 'ledger-cli', task: null, page: 'terminal', spot: '.role-requests, .pane-slot[data-role-request-pending]' },
      question: { agent: 'launch-41c7', spot: '.native-question, .app-notifications' },
      // 0.1.3 的三层视图：先停在项目的任务分屏，再像点了 T-11 那样进入它的 agent 分屏。
      views: { project: 'inkwell', task: null, page: 'terminal', spot: '.project-task-tile[data-task-tile="T-11"]',
        then: { task: 'T-11', spot: '.pane-layout, .gate' } },
      // 泳道比窗口宽（真实应用也是左右滚动）：先往右带一眼独立审查和集成，停一会儿再回到泳道开头。
      // 首屏展示把三层视图拆成两步：项目的任务格，点一张票后的 agent 分屏。
      grid: { project: 'inkwell', task: null, page: 'terminal', spot: '.project-task-tile[data-task-tile="T-11"]' },
      panes: { project: 'inkwell', task: 'T-11', page: 'terminal', spot: '.pane-layout, .gate' },
      flow: { project: 'inkwell', page: 'flow', spot: '.flow-lane[data-flow-task="T-11"]', play: [
        [1500, () => { const lanes = root.querySelector('.flow-scroll'); lanes?.scrollTo({ left: lanes.scrollWidth, behavior: 'smooth' }); }],
        [4300, () => root.querySelector('.flow-scroll')?.scrollTo({ left: 0, behavior: 'smooth' })]] },
      issues: { project: 'inkwell', page: 'issues', spot: '.issue-card[data-issue-id="i-2"]' },
      records: { project: 'inkwell', page: 'records', spot: '.record-table' },
      metrics: { project: 'inkwell', page: 'metrics', spot: '.metric-section[data-metric="first-time"]' },
      reflect: { project: 'inkwell', page: 'reflect', spot: '.reflect-tree' },
      settings: { settings: true, spot: '.execution-settings' },
    };
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)');
    // 换场景时内容淡入、窗格依次出现；减弱动效时直接显示。
    function enter() {
      if (calm.matches) return;
      root.classList.remove('wb-enter'); void root.offsetWidth; root.classList.add('wb-enter');
      // render() 会重建内容；动画播完就去掉，之后在演示里点按不再重播。
      clearTimeout(enter.done); enter.done = setTimeout(() => root.classList.remove('wb-enter'), 900);
    }
    function go(name) {
      timers.forEach(clearTimeout); timers = [];
      if (name === 'reset') { reset(); render(); return; }
      const scene = scenes[name];
      if (!scene) return;
      // 通知只在讲它的两步出现，其余步骤当作已经看过，不盖住要讲的区域；问题本身仍等你回答。
      if (name !== 'sidebar' && name !== 'question') ui.noticeActive.clear();
      Object.assign(ui, { menu: null, note: null, settingsOpen: false, renaming: null, zoom: null, spot: scene.spot });
      if (scene.agent) selectAgent(scene.agent);
      if ('project' in scene) Object.assign(ui, { project: scene.project, focusedAgent: null, focusedPane: null });
      if ('task' in scene) ui.task = scene.task;
      else if (scene.project && !findProject(scene.project).tasks.some(task => task.id === ui.task)) ui.task = null;
      if (scene.page) ui.page = scene.page;
      if (scene.settings) ui.settingsOpen = true;
      const then = scene.then;
      if (then && calm.matches) Object.assign(ui, then);
      render(); enter();
      if (scene.play && !calm.matches) for (const [delay, step] of scene.play) timers.push(setTimeout(() => { if (ui.page === scene.page) step(); }, delay));
      if (then && !calm.matches) timers.push(setTimeout(() => { if (ui.project === scene.project && !ui.task) { Object.assign(ui, then); render(); enter(); } }, 1600));
      // 每一步从页面顶部看起。
      root.querySelectorAll('.records-page, .flow-page').forEach(el => { el.scrollTop = 0; });
      root.querySelectorAll('.flow-scroll').forEach(el => { el.scrollLeft = 0; });
    }

    reset();
    render();
    return { go, scenes: Object.keys(scenes) };
  }
  window.EnchantedDemo = { mount };
})();
