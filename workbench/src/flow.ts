import { sidebarSnapshot } from './sidebar.ts';
import type { RoleRequests } from './roleRequests.ts';
import type { OrchestrationStore } from './store.ts';

import type { FlowStage } from './flowStages.ts';
type GateEvent = { task: string; attempt: string | null; type: string; details: any };
export type FlowAgent = { id: string; project: string; task: string | null; attempt: string | null;
  parent: string | null; role: string; preset?: string | null; state: string; state_label?: string; role_label?: string; cli?: string;
  task_name?: string | null; unassigned_reason?: string };

// Events alone establish progression. Task rows supply identity and the current
// attempt, never an inferred stage. delivery_rejected is the single rejection
// fact emitted after failed verification/review, not every error or refusal.
export function projectFlow(tasks: any[], agents: FlowAgent[], events: GateEvent[],
  projects: { project_id: string; repo: string | null; extra_directories: string[] }[] = []) {
  const assigned = new Set<string>();
  const lanes = tasks.map(task => {
    let stage: FlowStage | null = null, integrated = false;
    const returns = events.filter(event => event.task === task.task_id && event.type === 'delivery_rejected')
      .map((event, index) => ({ from: event.details.repair?.check === 'independent_review' ? 'review' as const : 'checks' as const, seq: index + 1 }));
    for (const event of events.filter(event => event.task === task.task_id && event.attempt === (task.current_attempt?.attempt_id ?? null))) {
      const data = event.details;
      switch (event.type) {
        case 'created': case 'claimed': stage = 'implementation'; integrated = false; break;
        case 'submitted': stage = 'delivery'; break;
        case 'verification_intent': stage = 'checks'; break;
        case 'verification_result':
          stage = data.verification?.state === 'passed' ? 'review' : data.verification?.state === 'failed' ? 'checks' : null;
          break;
        case 'review_requested': case 'review_started': stage = 'review'; break;
        case 'review_result': stage = data.review?.state === 'passed' ? 'integration' : 'review'; break;
        case 'delivery_rejected':
          stage = data.repair?.stopped ? null : 'implementation'; break;
        case 'review_reused': case 'integration_intent': stage = 'integration'; break;
        case 'integrated': case 'integrated_reconciled': stage = 'integration'; integrated = true; break;
        case 'verification_interrupted': case 'verification_conflict': case 'integration_conflict':
        case 'integration_compare_failed': stage = null; break;
      }
    }
    const bound = agents.filter(agent => typeof task.current_attempt?.attempt_id === 'string' && task.current_attempt.attempt_id.length > 0 &&
      agent.project === task.project_id && agent.task === task.task_id &&
      agent.attempt === task.current_attempt?.attempt_id && agent.parent &&
      ['worker', 'reviewer', 'monitor'].includes(agent.role));
    // The terminal's task is not delegation. Use the authenticated parent of
    // this lane's current worker, already checked by sidebarSnapshot.
    const controllers = agents.filter(agent => agent.project === task.project_id && agent.role === 'controller' &&
      agent.preset === 'executor' && bound.some(child => child.role === 'worker' && child.parent === agent.id));
    const members = [...controllers, ...bound];
    members.forEach(agent => assigned.add(agent.id));
    const project = projects.find(project => project.project_id === task.project_id);
    const paths = [...new Set<string>([project?.repo ?? task.repo, ...(project?.extra_directories ?? [])]
      .filter((path): path is string => typeof path === 'string' && path.length > 0))];
    return { task: task.task_id, name: task.name, project: task.project_id, title: task.title, attempt: task.current_attempt?.attempt_id ?? null,
      paths, stage, integrated, returns,
      agents: members.filter(agent => agent.role !== 'monitor').map(agent => ({ ...agent, task_name: task.name })),
      monitors: bound.filter(agent => agent.role === 'monitor').map(agent => ({ ...agent, task_name: task.name })) };
  });
  return { lanes, unassigned: agents.filter(agent => !assigned.has(agent.id)).map(agent => ({ ...agent,
    unassigned_reason: agent.role === 'controller'
      ? agent.preset === 'executor' ? '没有关联到当前任务 attempt 的派发 worker' : '构思主控属于项目，不归属任务阶段'
      : !tasks.some(task => task.task_id === agent.task && task.project_id === agent.project) ? '项目或任务无法对应'
      : !agent.parent ? '缺少已核实的父会话关系' : '无法对应任务的当前 attempt 或阶段角色' })) };
}
export type FlowSnapshot = ReturnType<typeof projectFlow>;

export async function flowSnapshot(gates: any, store: OrchestrationStore, panes: any, roleRequests: RoleRequests): Promise<FlowSnapshot> {
  const sidebar = await sidebarSnapshot(gates, store, panes, roleRequests);
  const tasks = gates.db.prepare('SELECT data FROM tasks ORDER BY id').all().map((row: any) => JSON.parse(String(row.data)));
  const events = gates.db.prepare('SELECT task,attempt,type,details FROM events ORDER BY seq').all()
    .map((row: any) => ({ ...row, details: JSON.parse(String(row.details)) }));
  return projectFlow(tasks, sidebar.agents, events, sidebar.projects);
}
