import { useEffect, useState } from 'react';
import { flowStages } from '../src/flowStages.ts';
import type { FlowAgent, FlowSnapshot } from '../src/flow.ts';
import './flow.css';

const icons: Record<string, string> = { running: '●', waiting_user_answer: '◐', waiting_controller_answer: '◑', idle: '○', ended: '✓', unrestored: '◌', unknown: '?' };
const colors = ['#58b9a7', '#b29af5', '#70a9f0', '#eda456', '#e685a6', '#78c98d'];
function Agents({ agents, group }: { agents: FlowAgent[]; group: string }) {
  const [expanded, setExpanded] = useState(false);
  return <div className="flow-agents">
    {(expanded ? agents : agents.slice(0, 4)).map((agent, index) => <div className="flow-agent" key={agent.id}
      data-flow-agent={agent.id} data-flow-role={agent.role} data-flow-state={agent.state}>
      <span className="flow-dot" aria-hidden="true" style={{ background: colors[index % colors.length] }} />
      <span><strong>{agent.id}</strong><small>{agent.role_label ?? agent.role} · {agent.cli ?? 'CLI 未知'} · {agent.attempt ?? 'attempt 未知'}</small>
        <small><span aria-hidden="true">{icons[agent.state] ?? '?'}</span> {agent.state_label ?? '未知'}</small></span>
    </div>)}
    {agents.length > 4 && <button className="flow-more" data-flow-more={group} aria-expanded={expanded}
      onClick={() => setExpanded(value => !value)}>{expanded ? '收起' : `还有 ${agents.length - 4} 个 ↗`}</button>}
  </div>;
}
function Lane({ lane }: { lane: FlowSnapshot['lanes'][number] }) {
  const [open, setOpen] = useState(!lane.integrated);
  const current = flowStages.findIndex(stage => stage.id === lane.stage);
  return <article className="flow-lane" data-flow-task={lane.task} data-flow-stage={lane.stage ?? 'unknown'}>
    <header className="flow-lane-heading"><button data-flow-toggle={lane.task} aria-expanded={open} onClick={() => setOpen(value => !value)}>
      <span aria-hidden="true">{open ? '⌄' : '›'}</span> {lane.task} · {lane.title}</button>
      <span>{lane.project} · {lane.integrated ? '已集成' : current < 0 ? '阶段未知 · 核对门禁记录' : flowStages[current].label}
        {lane.returns.length > 0 && ` · 打回 ${lane.returns.length} 次`}</span></header>
    {open && <div className="flow-lane-body">
      {lane.monitors.length > 0 && <div className="flow-monitors"><span>贯穿监视</span><Agents agents={lane.monitors} group={lane.task + '-monitors'} /></div>}
      <div className="flow-stages">
        {lane.returns.length > 0 && <div className="flow-returns" aria-label={`打回 ${lane.returns.length} 次`}>
          {(['checks', 'review'] as const).map(from => {
            const count = lane.returns.filter(item => item.from === from).length;
            return count > 0 && <div className={'flow-return from-' + from} key={from} data-flow-return={from} data-return-count={count}>
              <span>↶ {from === 'review' ? '审查' : '机械检查'}打回 {count} 次</span></div>;
          })}
        </div>}
        {flowStages.map((stage, index) => <section key={stage.id} data-flow-column={stage.id}
          className={'flow-stage ' + (lane.integrated || index < current ? 'complete' : index === current ? 'current' : '')}
          aria-label={stage.label} aria-current={index === current && !lane.integrated ? 'step' : undefined}>
          <div className="flow-track" aria-hidden="true"><i />{index < flowStages.length - 1 && <span>›››</span>}</div>
          <h3>{stage.label}</h3>
          <Agents agents={lane.agents.filter(agent => stage.id === (agent.role === 'reviewer' ? 'review' : 'implementation'))} group={lane.task + '-' + stage.id} />
        </section>)}
      </div>
    </div>}
  </article>;
}
export function FlowPage() {
  const [snapshot, setSnapshot] = useState<FlowSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let disposed = false, timer: ReturnType<typeof setTimeout>;
    const refresh = async () => {
      try { const value = await window.a2a.flow(); if (!disposed) { setSnapshot(value); setError(null); } }
      catch (failure) { if (!disposed) setError('读取流程失败：' + String(failure)); }
      finally { if (!disposed) timer = setTimeout(refresh, 1500); }
    };
    void refresh();
    return () => { disposed = true; clearTimeout(timer); };
  }, []);
  return <section className="flow-page" aria-label="系统流程">
    <div className="flow-intro"><h2>系统流程</h2><p>一张票一条泳道 · 阶段来自门禁记录 · agent 只按已保存的归属展示</p>
      <p className="flow-legend">● 运行中　◐ 等待用户回答　◑ 等待主控回答　○ 空闲　✓ 已结束　◌ 未恢复　? 未知</p></div>
    {error && <p role="alert">{error}{snapshot && '（保留上次记录）'}</p>}
    {!snapshot && !error && <p role="status">正在读取流程…</p>}
    {snapshot && <>
      {!snapshot.lanes.length && <p className="flow-empty" role="status">还没有任务票。注册任务后，流程会显示在这里。</p>}
      <div className="flow-scroll" tabIndex={0} aria-label="任务泳道，可左右滚动">
        {snapshot.lanes.map(lane => <Lane key={lane.task} lane={lane} />)}
      </div>
      {snapshot.unassigned.length > 0 && <section className="flow-unassigned" aria-label="未归属"><h3>未归属</h3>
        <p>父记录、任务或当前 attempt 无法对应，或角色不属于票内阶段的会话。</p><Agents agents={snapshot.unassigned} group="unassigned" /></section>}
    </>}
  </section>;
}
