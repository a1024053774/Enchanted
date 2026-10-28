// T-205: a refusal code alone left the user and the controller guessing. Common codes get one line of why and one line of
// what to do next. The daemon adds it to every refused reply (a2a, MCP and the window read the same reply); the task page
// and the worker's receipt read the same table. The code itself stays the contract; codes not listed get no explanation.
export type RefusalExplanation = { reason: string; next: string };

const staleRunner: RefusalExplanation = {
  reason: '请求来自已经不是当前执行者的 attempt 或会话：任务已改卡、回收或重派。',
  next: 'worker 结束本回合，不再交付；主控用 status 看当前的 attempt。',
};

const explanations: Record<string, RefusalExplanation> = {
  invalid_task_card: { reason: '任务卡有字段不合规，回执的 field 与 reason 指出是哪一项。', next: '按 field 与 reason 改好卡文件，再 card_save。' },
  task_exists: { reason: '门禁里已经有同名任务。', next: '新任务换一个任务号；要改已有任务的卡，用 card_save 存新版本再 revise。' },
  unknown_task: { reason: '门禁里没有这个任务。', next: '核对任务名；别的项目的任务写完整 id：<项目>+<任务>。' },
  project_not_opened: { reason: '目标项目没有在工作台里打开，回执列出已打开的项目。', next: '请用户先在工作台打开这个项目，再重试。' },
  controller_required: { reason: '这条命令只有已批准的主控能用。', next: '用户要你当主控时，运行 a2a request 申请，等用户在 Enchanted 里批准。' },
  executor_required: { reason: '这一步只能由执行主控做。', next: '交给执行主控，或在用户同意后申请执行主控。' },
  oracle_not_found: { reason: '任务卡 oracle_paths 列的验收文件不在基线提交里（还没提交进 Git，或路径写错），回执的 missing 列出是哪些。',
    next: '把验收文件提交到工作分支，或把卡里的路径改对，再派发。' },
  path_overlap: { reason: '这张卡允许改的路径与进行中的任务重叠，回执的 conflicts 列出与谁重叠。',
    next: '能并行就重发同一条 dispatch 并写 overlap_reason；不能就等对方验收或回收后再派。' },
  command_unavailable: { reason: '门禁要运行的命令没能启动（程序不存在或不可执行），回执的 details 里有命令与原因。',
    next: '按 details 核对命令；是任务卡里的命令就改卡后重试。' },
  run_blocked: { reason: 'worker 的 CLI 停在确认框、权限请求或其他提示上，门禁没法继续，这时回收也会被拒。',
    next: '到 worker 窗格看它停在哪个提示上，由用户处理后再继续。' },
  worker_working: { reason: '会话还在回合中，门禁不在它工作时回收或停止它。', next: '等它这一回合结束后再试。' },
  stale_turn: { reason: '这个 attempt 已经交付过；交付被打回（验收或审查判“需修复”）之前，不能再交。',
    next: 'worker 结束本回合。要补改：主控改卡后按“card_save 存新卡 → revise → reclaim 旧 attempt → dispatch”重派。' },
  stale_attempt: staleRunner,
  stale_session: staleRunner,
  stale_fence: staleRunner,
  stale_thread: staleRunner,
  stale_spec: { reason: '任务卡已经更新（revise），这次交付按的是旧版本。', next: 'worker 结束本回合，不再交付；主控按新卡重派。' },
  not_submitted: { reason: '任务还没有交付，不能验收。', next: '用 status 看进度，等状态变成“已交付”再 verify。' },
  repair_submission_required: { reason: '上一次交付已被打回，任务在等 worker 修好后重交，现在不能验收。', next: '等 worker 重新交付后再 verify。' },
  quality_rejection_limit: { reason: '同一个 attempt 被打回的次数到了上限，门禁不再接受它的修复。',
    next: '主控改卡后回收并重派，或关闭这个任务。' },
  oracle_failed: { reason: '完成条件在这次交付上没有通过，交付已打回给 worker 修复。', next: '用 status 看失败输出，等 worker 修好重交。' },
  not_verified: { reason: '任务还没有通过验收与独立审查，不能集成。', next: '先 verify，等审查结论“可合并”、状态变成“验收通过”再集成。' },
  out_of_card_unjudged: { reason: '交付改了任务卡没允许的文件，主控还没判断留不留。',
    next: '主控用 out_of_card 写 accept 或 reject 和理由，再集成。' },
  score_required: { reason: '集成要附主控的打分文件。', next: '把打分写成 JSON 文件，integrate 时带上 score_file。' },
  already_accepted: { reason: '任务已经集成。', next: '不用再做；有新的改动就另建任务。' },
  task_closed: { reason: '任务已经关闭，不能再派发或改动。', next: '需要的话另建任务。' },
};

export function explainRefusal(code: unknown): RefusalExplanation | null {
  return typeof code === 'string' && Object.hasOwn(explanations, code) ? explanations[code] : null;
}
