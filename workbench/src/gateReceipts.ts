import { explainRefusal } from './gates/refusals.ts';

// T-179: a gate receipt in a few lines a person can read in the worker's pane: the command, whether the gate took it,
// the task's state and candidate commit, and the next step. The full receipt stays in relay_results and on the records page.
export const gateStateNames: Record<string, string> = { creating: '创建中', ready: '待认领', preparing: '准备中', claimed: '已认领', submitted: '已交付',
  verifying: '验收中', verified: '验收通过', reviewing: '审查中', rework: '返工中', integrating: '集成中', accepted: '已集成', paused: '已暂停', revoked: '已撤销',
  abandoned: '已放弃', upgraded: '已升级', closed: '已关闭' };
const commandNames: Record<string, string> = { submit: '交付', status: '查状态', issue: '上报问题', review_submit: '提交审查结论' };

export function receiptLines(command: string | null, result: any): string[] {
  const name = commandNames[command ?? ''] ?? command ?? '请求';
  if (!result?.ok) {
    const refused = `${name}：门禁没有受理（${result?.error ?? '原因未知'}）`, why = explainRefusal(result?.error);
    if (why) return [refused, '原因：' + why.reason, '下一步：' + why.next];
    return [refused, '下一步：结束本回合；要改什么由门禁或主控另行说明。'];
  }
  const lines = [`${name}：门禁已受理`];
  const task = result.task;
  if (task) lines.push(`任务 ${task.name ?? task.task_id} · ${gateStateNames[task.state] ?? task.state} · ${
    task.candidate_commit ? `候选提交 ${String(task.candidate_commit).slice(0, 12)}` : '还没有候选提交'}`);
  if (command === 'issue' && result.number !== undefined) lines.push(`问题编号 #${result.number}`);
  lines.push('下一步：' + (command === 'submit' ? '等主控验收；本回合不用再做什么。' : '结束本回合。'));
  return lines;
}
