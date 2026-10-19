import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import type { OrchestrationStore } from './store.ts';

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
export function agentState(pane: any, events: any[]): AgentState {
  if (pane?.restoration && ['failed', 'pending'].includes(pane.restoration.status)) return 'unrestored';
  if (pane?.lifecycle === 'ended') return 'ended';
  if (!pane || pane.historical || pane.failed || pane.interrupted || pane.lifecycle !== 'running') return 'unknown';
  const pending = new Set<string>();
  let permission = false;
  for (const event of events) {
    if (event.type === 'permission_wait') permission = true;
    if (['turn_start_signal', 'pane_idle'].includes(event.type)) permission = false;
    const record = event.data?.record, payload = record?.payload;
    if (record?.type === 'response_item' && payload?.type === 'function_call' &&
        ['request_user_input', 'request_user_input_async'].includes(payload.name)) pending.add(payload.call_id);
    // Async acceptance is not an answer. Without a verified answer format this
    // call remains unknown; T-095's Herdr screen corroboration is unavailable.
    // A response alone is not a verified answer (e.g. async accepted:true).
    // Leave this state unknown until a later native turn supersedes it.
    if (record?.type === 'event_msg' && payload?.type === 'task_started') pending.clear();
  }
  if (permission || pending.size) return 'unknown';
  if (pane.state === 'idle' && !pane.active && !pane.writing) return 'idle';
  const submission = events.findLast(event => event.type === 'turn_submitted' && event.data?.id === pane.active?.id);
  if (pane.state === 'busy' && pane.active && !pane.writing && pane.native_session &&
      (pane.active.nativeTurn && pane.turn === pane.active.nativeTurn || submission && events.some(event =>
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
      { timeout: 3000, maxBuffer: 65536, env: { ...process.env, GIT_OPTIONAL_LOCKS: '0' } });
    const lines = stdout.split('\n');
    const field = (key: string) => lines.find(line => line.startsWith('# branch.' + key + ' '))?.slice(('# branch.' + key + ' ').length);
    const branch = field('head'), upstream = field('upstream'), ab = field('ab')?.match(/^\+([0-9]+) -([0-9]+)$/);
    if (!branch || upstream && !ab) return { branch: null, upstream: null, ahead: null, behind: null, error: 'Git 分支事实不完整' };
    return { branch, upstream: upstream ?? null, ahead: ab ? Number(ab[1]) : null, behind: ab ? Number(ab[2]) : null, error: null };
  } catch (error) {
    return { branch: null, upstream: null, ahead: null, behind: null, error: '无法读取 Git：' + String(error) };
  }
}

export async function sidebarSnapshot(gates: any, store: OrchestrationStore, panes: any) {
  const launches = store.launches().filter(record => record.role !== 'shell');
  const assignments = store.db.prepare(`SELECT d.launch,q.launch AS parent,q.input,r.data AS result
    FROM dispatch_records d JOIN relay_results r ON json_extract(r.data,'$.entry.id')=json_extract(d.data,'$.inbox_entry')
    JOIN relay_requests q ON q.key=r.key
    WHERE json_extract(r.data,'$.ok')=1 AND json_extract(q.input,'$.command')='inbox_send'
      AND json_extract(q.input,'$.kind')='assign' ORDER BY d.seq`).all();
  // status() uses the existing native reader. Read events afterwards so a newly
  // observed question cannot be missed while promoting the same read to running.
  const statuses = new Map(launches.map(record => [record.id, panes.status(record.thread)]));
  const events = store.db.prepare(`SELECT seq,type,launch,data FROM orchestration_events
    WHERE type IN ('permission_wait','turn_start_signal','turn_submitted','pane_idle')
      OR type='native_record' AND json_extract(data,'$.record.payload.type') IN ('function_call','task_started')
    ORDER BY seq`).all().map(row => ({ ...row, data: JSON.parse(String(row.data)) }));
  const agents = launches.map(record => {
    // A role address or an ordinary reply is not delegation. Correlate the
    // authenticated sender launch, successful assign and actual dispatch target.
    const senders = new Set<string>();
    for (const assignment of assignments.filter(row => row.launch === record.id)) {
      const parent = launches.find(row => row.id === assignment.parent);
      const input = JSON.parse(String(assignment.input)), result = JSON.parse(String(assignment.result));
      const recipient = record.role === 'controller' ? record.preset : `${record.role}:${record.thread}`;
      if (parent && parent.id !== record.id && parent.project === record.project && input.launch === parent.id &&
          input.project === parent.project && input.task === parent.task && input.preset === parent.preset &&
          result.entry?.kind === 'assign' && result.entry.from === parent.preset && result.entry.to === recipient) senders.add(parent.id);
    }
    const state = agentState(statuses.get(record.id), events.filter(event => event.launch === record.id));
    return { id: record.id, project: record.project, task: record.task, attempt: record.attempt, thread: record.thread,
      role: record.role, preset: record.preset ?? null, role_label: roleLabel(record),
      cli: record.cli === 'Claude Code' || record.cli_version?.startsWith('Claude Code') ? 'claude' :
        record.cli_version?.startsWith('codex-cli ') ? 'codex' : '未知',
      parent: senders.size === 1 ? [...senders][0] : null, state, state_label: stateLabels[state] };
  });
  for (const agent of agents) {
    const parent = agents.find(row => row.id === agent.parent);
    const allowed = parent?.preset === 'ideation' && agent.preset === 'executor' ||
      parent?.preset === 'executor' && ['worker', 'reviewer', 'monitor'].includes(agent.role);
    if (!allowed) agent.parent = null;
    const visited = new Set([agent.id]);
    let cursor = agent.parent;
    while (cursor) {
      if (visited.has(cursor)) { agent.parent = null; break; }
      visited.add(cursor); cursor = agents.find(row => row.id === cursor)?.parent ?? null;
    }
  }
  const projects = await Promise.all(gates.listProjects().map(async (project: any) => {
    const tasks = gates.listTasks(project.project_id);
    const repos = new Set<string>();
    for (const task of tasks) {
      const result = await gates.call({ command: 'status', task: task.task_id });
      if (!result.ok) throw new Error('Task catalog changed: ' + task.task_id);
      repos.add(result.task.repo);
    }
    const repo = repos.size === 1 ? [...repos][0] : null;
    const state = aggregate(agents.filter(agent => agent.project === project.project_id).map(agent => agent.state));
    return { ...project, repo, tasks, git: repo ? await gitFacts(repo) :
      { branch: null, upstream: null, ahead: null, behind: null, error: '项目目录不唯一' }, state, state_label: stateLabels[state] };
  }));
  return { projects, agents, gaps: [
    '等待用户回答：工作台现有信号不能可靠区分，当前显示未知；未新增采集。',
    '等待主控回答：T-095 需要 Herdr 屏幕与状态互证；本工作台不调用 Herdr，当前显示未知。',
    '派发未保存具体父会话绑定时显示未归属；当前 worker 派发缺少该绑定。',
  ] };
}
