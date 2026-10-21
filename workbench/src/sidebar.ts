import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { codexSessionOrigin } from './paneRecovery.ts';
import type { OrchestrationStore } from './store.ts';
import { questionState, projectQuestions } from './questions.ts';
import type { RoleRequests } from './roleRequests.ts';

export type AgentState = 'running' | 'waiting_user_answer' | 'waiting_controller_answer' | 'idle' | 'ended' | 'unrestored' | 'unknown';
export const stateLabels: Record<AgentState, string> = {
  running: '运行中', waiting_user_answer: '等待用户回答', waiting_controller_answer: '等待主控回答',
  idle: '空闲', ended: '已结束', unrestored: '未恢复', unknown: '未知',
};
export const roleLabel = (record: any): string => record.role === 'controller'
  ? record.preset === 'ideation' ? '构思主控' : record.preset === 'executor' ? '执行主控' : '角色未知'
  : ({ worker: 'worker', reviewer: '审查员', monitor: '监视器' }[record.role] ?? '角色未知');

// busy includes permissions, interruptions and a submitted but unobserved turn.
// Only an active, correlated native turn is positive execution evidence.
export function agentState(pane: any, events: any[], worktree: string | undefined): AgentState {
  if (pane?.restoration && ['failed', 'pending'].includes(pane.restoration.status)) return 'unrestored';
  if (pane?.lifecycle === 'ended') return 'ended';
  if (!pane || pane.historical || pane.failed || pane.interrupted || pane.lifecycle !== 'running') return 'unknown';
  const waiting = questionState(pane, events);
  if (waiting) return waiting;
  const resolvedQuestions = new Set(projectQuestions(events).filter(q => ['answered', 'cancelled'].includes(q.status)).map(q => q.tool_use_id));
  const pending = new Set<string>();
  const files = new Map<string, { kind: ReturnType<typeof codexSessionOrigin>; turn: string | null }>();
  let uncertainQuestion = false;
  let permission = false;
  for (const event of events) {
    if (event.type === 'permission_wait') permission = true;
    if (event.type === 'turn_start_signal' && event.data?.session_id === pane.native_session ||
        event.type === 'pane_idle' && event.data?.stop?.session_id === pane.native_session) permission = false;
    const record = event.data?.record, payload = record?.payload;
    if (event.type !== 'native_record') continue;
    const file = event.data?.file;
    if (record?.type === 'session_meta' && typeof file === 'string') {
      files.set(file, { kind: codexSessionOrigin(file, record, pane.native_session, worktree), turn: null });
    }
    const origin = files.get(file);
    if (record?.type === 'event_msg' && payload?.type === 'task_started' && origin?.kind === 'root' && typeof payload.turn_id === 'string') {
      origin.turn = payload.turn_id;
    }
    if (record?.type === 'response_item' && payload?.type === 'function_call' &&
        ['request_user_input', 'request_user_input_async'].includes(payload.name)) {
      if (origin?.kind === 'root' && origin.turn === pane.turn &&
          (!payload.internal_chat_message_metadata_passthrough || payload.internal_chat_message_metadata_passthrough.turn_id === origin.turn)) {
        if (!resolvedQuestions.has(payload.call_id)) pending.add(payload.call_id);
      }
      else if (origin?.kind !== 'auxiliary') uncertainQuestion = true;
    }
    // Neither a new turn nor an async accepted:true proves an answer. Keep
    // unresolved/uncorrelated questions unknown until answer evidence exists.
  }
  if (permission || pending.size || uncertainQuestion) return 'unknown';
  if (pane.state === 'idle' && !pane.active && !pane.writing) return 'idle';
  const roots = [...files.values()].filter(origin => origin.kind === 'root');
  const rootTurnObserved = roots.length === 1 && roots[0].turn === pane.turn;
  if (roots.length > 1) return 'unknown';
  const submission = events.findLast(event => event.type === 'turn_submitted' && event.data?.id === pane.active?.id);
  if (pane.state === 'busy' && pane.active && !pane.writing && pane.native_session &&
      (rootTurnObserved && pane.active.nativeTurn && pane.turn === pane.active.nativeTurn || submission && events.some(event =>
        event.seq > submission.seq && event.type === 'turn_start_signal' && event.data?.session_id === pane.native_session))) return 'running';
  return 'unknown';
}

export function aggregate(states: AgentState[]): AgentState {
  if (states.includes('waiting_user_answer')) return 'waiting_user_answer';
  if (states.includes('waiting_controller_answer')) return 'waiting_controller_answer';
  if (states.includes('running')) return 'running';
  if (!states.length || states.includes('unknown')) return 'unknown';
  if (states.includes('unrestored')) return 'unrestored';
  return states.includes('idle') ? 'idle' : 'ended';
}

const execute = promisify(execFile);
export async function gitFacts(repo: string) {
  try {
    const { stdout } = await execute('git', ['-C', repo, 'status', '--porcelain=v2', '--branch', '--untracked-files=no'],
      { timeout: 3000, maxBuffer: 65536, env: { ...process.env, LC_ALL: 'C', GIT_OPTIONAL_LOCKS: '0' } });
    const lines = stdout.split('\n');
    const field = (key: string) => lines.find(line => line.startsWith('# branch.' + key + ' '))?.slice(('# branch.' + key + ' ').length);
    const branch = field('head'), upstream = field('upstream'), ab = field('ab')?.match(/^\+([0-9]+) -([0-9]+)$/);
    if (!branch || upstream && !ab) return { branch: null, upstream: null, ahead: null, behind: null, error: 'Git 分支事实不完整' };
    return { branch, upstream: upstream ?? null, ahead: ab ? Number(ab[1]) : null, behind: ab ? Number(ab[2]) : null, error: null };
  } catch (error) {
    return { branch: null, upstream: null, ahead: null, behind: null, error: '无法读取 Git：' + String(error) };
  }
}

// A project is a directory the user opened, or a gate project that has tasks.
// An opened directory names the project's repo; otherwise the tasks must agree.
export async function projectCatalog(gates: any, store: OrchestrationStore) {
  const opened = new Map(store.openedProjects().map(project => [project.project_id, project.repo]));
  const ids = [...new Set([...gates.listProjects().map((project: any) => String(project.project_id)), ...opened.keys()])].sort();
  return Promise.all(ids.map(async project_id => {
    const tasks = gates.listTasks(project_id);
    const repos = new Set<string>();
    for (const task of tasks) {
      const result = await gates.call({ command: 'status', task: task.task_id });
      if (!result.ok) throw new Error('Task catalog changed: ' + task.task_id);
      repos.add(result.task.repo);
    }
    const repo = opened.get(project_id) ?? (repos.size === 1 ? [...repos][0] : null);
    return { project_id, repo, tasks, opened: opened.has(project_id) };
  }));
}

export async function sidebarSnapshot(gates: any, store: OrchestrationStore, panes: any, roleRequests: RoleRequests) {
  const launches = store.launches().filter(record => record.role !== 'shell');
  const assignments = store.db.prepare(`SELECT d.launch,q.launch AS parent,q.input,r.data AS result
    FROM dispatch_records d JOIN relay_results r ON json_extract(r.data,'$.entry.id')=json_extract(d.data,'$.inbox_entry')
    JOIN relay_requests q ON q.key=r.key
    WHERE json_extract(r.data,'$.ok')=1 AND json_extract(q.input,'$.command')='inbox_send'
      AND json_extract(q.input,'$.kind')='assign' ORDER BY d.seq`).all();
  // status() is a pure snapshot. Native collection belongs to PTY/hook/process
  // observation; a sidebar query consumes only already persisted facts.
  const statuses = new Map(launches.map(record => [record.id, panes.status(record.thread)]));
  const events = store.db.prepare(`SELECT seq,type,launch,data FROM orchestration_events
    WHERE type IN ('permission_wait','permission_control_written','turn_start_signal','turn_submitted','pane_idle',
      'native_question_opened','native_question_resolved','native_question_answer_intent','native_question_unverified')
      OR type='native_record' AND (json_extract(data,'$.record.type')='session_meta'
        OR json_extract(data,'$.record.payload.type') IN ('function_call','task_started'))
    ORDER BY seq`).all().map(row => ({ ...row, data: JSON.parse(String(row.data)) }));
  const agents = launches.map(record => {
    // A role address or an ordinary reply is not delegation. Correlate the
    // authenticated sender launch, successful assign and actual dispatch target.
    const senders = new Set<string>();
    if (typeof record.parent_launch === 'string') senders.add(record.parent_launch);
    for (const assignment of assignments.filter(row => row.launch === record.id)) {
      const parent = launches.find(row => row.id === assignment.parent);
      const input = JSON.parse(String(assignment.input)), result = JSON.parse(String(assignment.result));
      const recipient = record.role === 'controller' ? record.preset : `${record.role}:${record.thread}`;
      if (parent && parent.id !== record.id && parent.project === record.project && input.launch === parent.id &&
          input.project === parent.project && input.task === parent.task && input.preset === parent.preset &&
          result.entry?.kind === 'assign' && result.entry.from === parent.preset && result.entry.to === recipient) senders.add(parent.id);
    }
    const launchEvents = events.filter(event => event.launch === record.id);
    const state = agentState(statuses.get(record.id), launchEvents, record.worktree);
    const question_id = state === 'waiting_user_answer'
      ? projectQuestions(launchEvents).find(question => question.status === 'waiting' &&
        question.submission === statuses.get(record.id)?.active?.id)?.id ?? null : null;
    return { id: record.id, project: record.project, task: record.task, attempt: record.attempt, thread: record.thread,
      role: record.role, preset: record.preset ?? null, role_label: roleLabel(record),
      cli: record.cli === 'Claude Code' || record.cli_version?.startsWith('Claude Code') ? 'claude' :
        record.cli_version?.startsWith('codex-cli ') ? 'codex' : '未知',
      parent: senders.size === 1 ? [...senders][0] : null, state, question_id, state_label: stateLabels[state],
      created_at: record.created_at ?? null };
  });
  // T-121: a terminal whose CLI the user approved as a controller. It has no task
  // and no structured turn signals yet, so its state stays unknown.
  const current = roleRequests.all();
  for (const roleRequest of current.filter(row => row.state === 'approved')) {
    const record = store.launchRecord(roleRequest.launch);
    if (!record) continue;
    agents.push({ id: roleRequest.launch, project: roleRequest.project, task: null, attempt: null, thread: record.thread,
      role: 'controller', preset: roleRequest.role, role_label: roleLabel({ role: 'controller', preset: roleRequest.role }), cli: roleRequest.cli ?? '未知',
      parent: null, state: 'unknown', question_id: null, state_label: stateLabels.unknown, created_at: roleRequest.decided_at, terminal: true } as any);
  }
  const recordedParents = new Map(agents.map(agent => [agent.id, agent.parent]));
  for (const agent of agents) {
    const parent = agents.find(row => row.id === agent.parent);
    const allowed = parent?.project === agent.project && parent.role === 'controller' &&
      (parent.preset === 'ideation' && agent.role === 'controller' && agent.preset === 'executor' ||
       parent.preset === 'executor' && ['worker', 'reviewer', 'monitor'].includes(agent.role));
    if (!allowed) agent.parent = null;
    const visited = new Set([agent.id]);
    let cursor = recordedParents.get(agent.id);
    while (cursor) {
      if (visited.has(cursor)) { agent.parent = null; break; }
      visited.add(cursor); cursor = recordedParents.get(cursor) ?? null;
    }
  }
  const descendants = (id: string): typeof agents => agents.filter(child => child.parent === id)
    .flatMap(child => [child, ...descendants(child.id)]);
  const treeAgents = agents.map(agent => {
    const children = descendants(agent.id);
    const state = aggregate(children.map(child => child.state));
    return { ...agent, descendants: { count: children.length, state, state_label: stateLabels[state],
      counts: Object.keys(stateLabels).filter(key => children.some(child => child.state === key))
        .map(key => ({ state: key, label: stateLabels[key as AgentState], count: children.filter(child => child.state === key).length })) } };
  });
  const projects = await Promise.all((await projectCatalog(gates, store)).map(async project => {
    const state = aggregate(agents.filter(agent => agent.project === project.project_id).map(agent => agent.state));
    return { ...project, git: project.repo ? await gitFacts(project.repo) :
      { branch: null, upstream: null, ahead: null, behind: null, error: '项目目录不唯一' }, state, state_label: stateLabels[state] };
  }));
  // The terminal's directory and opening time tell two requests apart when their panes are out of view.
  const requestView = (row: typeof current[number]) => {
    const terminal = store.launchRecord(row.launch);
    return { id: row.id, launch: row.launch, project: row.project, role: row.role, role_label: roleLabel({ role: 'controller', preset: row.role }),
      cli: row.cli, requested_at: row.requested_at, terminal_cwd: terminal?.worktree ?? null, terminal_opened_at: terminal?.created_at ?? null };
  };
  const pendingRequests = current.filter(row => row.state === 'pending').map(requestView);
  const grantedRequests = current.filter(row => row.state === 'granted').map(requestView);
  // A grant that never took effect (not confirmed, or its asker left): tell the user, until
  // that terminal asks again or five minutes pass.
  const unconfirmed = current.filter(row => row.state === 'ended' && row.decided_at !== null &&
    ['not_confirmed', 'asker_gone'].includes(row.ended_reason ?? '') && Date.now() - Date.parse(row.decided_at) < 5 * 60_000 &&
    !current.some(later => later.launch === row.launch && Date.parse(later.requested_at) > Date.parse(row.requested_at)))
    .map(row => ({ ...requestView(row), decided_at: row.decided_at }));
  return { projects, agents: treeAgents, role_requests: pendingRequests, granted_role_requests: grantedRequests, unconfirmed_role_requests: unconfirmed, gaps: [
    '等待主控回答：T-095 需要 Herdr 屏幕与状态互证；本工作台不调用 Herdr，当前显示未知。',
    '未保存父 launch、父会话缺失或关系冲突时显示未归属；不回填旧会话。',
    '经角色申请成为主控的项目终端没有结构化回合信号，状态显示未知。',
  ] };
}
