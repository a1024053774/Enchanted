import { useEffect, useState } from 'react';
import { RetrospectiveSections } from './RetrospectiveSections';
import './records.css';

// T-137: the Reflect page, for looking back. Every controller this project ever had, the sessions started under it
// (ended ones included) with the score each worker's delivery got, then the retrospectives.
type ReflectNode = { id: string; kind: 'terminal' | 'managed'; launch: string; role: string; role_label: string; task: string | null;
  attempt: string | null; cli: string | null; model: string | null; effort: string | null; started_at: string | null; ended_at: string | null;
  state: string; state_label: string; parent: string | null; score: { data: { result: string; boundary_discipline?: number; boundary_reason?: string;
    engineering_taste?: number; engineering_reason?: string; notes?: string } } | null };
const time = (value: string | null) => value ? new Date(value).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';
const short = (task: string | null) => task ? task.slice(task.indexOf('+') + 1) : null;
const controller = (node: ReflectNode) => node.role === 'ideation' || node.role === 'executor';

function Score({ score }: { score: NonNullable<ReflectNode['score']> }) {
  const data = score.data;
  return <dl className="reflect-score" data-score-result={data.result}>
    <div><dt>结果</dt><dd>{data.result}</dd></div>
    {data.boundary_discipline !== undefined && <div><dt>边界纪律</dt><dd data-score-boundary={data.boundary_discipline}>{data.boundary_discipline}{data.boundary_reason ? `（${data.boundary_reason}）` : ''}</dd></div>}
    {data.engineering_taste !== undefined && <div><dt>工程品味</dt><dd data-score-taste={data.engineering_taste}>{data.engineering_taste}{data.engineering_reason ? `（${data.engineering_reason}）` : ''}</dd></div>}
    {data.notes && <div><dt>备注</dt><dd>{data.notes}</dd></div>}
  </dl>;
}

function Branch({ nodes, all, level }: { nodes: ReflectNode[]; all: ReflectNode[]; level: number }) {
  return <ul className="reflect-branch">{nodes.map(node => {
    const children = all.filter(child => child.parent === node.id);
    return <li key={node.id}>
      <div className="reflect-node" data-reflect-node={node.id} data-reflect-parent={node.parent ?? ''} data-reflect-level={level} data-reflect-state={node.state}
        data-reflect-launch={node.launch} style={{ paddingLeft: level * 18 }}>
        <div className="reflect-line">
          <strong>{node.role_label}</strong>
          <span className="record-meta">{node.kind === 'terminal' ? '项目终端' : short(node.task) ?? '项目级'}</span>
          <span className="record-meta">{[node.cli ?? 'CLI 未知', node.model ?? '模型未知', node.effort ?? '强度未知'].join(' · ')}</span>
          <span className="record-meta">{time(node.started_at)}{node.ended_at ? ` – ${time(node.ended_at)}` : ''}</span>
          <span className="record-state" data-tone={node.state === 'running' ? 'needs' : 'quiet'}>{node.state_label}</span>
        </div>
        {node.score && <Score score={node.score} />}
      </div>
      {children.length > 0 && <Branch nodes={[...children.filter(controller), ...children.filter(child => !controller(child))]} all={all} level={level + 1} />}
    </li>;
  })}</ul>;
}

export function ReflectPage({ project }: { project: string | null }) {
  const [nodes, setNodes] = useState<ReflectNode[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!project) return;
    let mounted = true;
    const load = () => window.a2a.reflect(project).then((value: ReflectNode[]) => { if (mounted) { setNodes(value); setError(null); } },
      (reason: unknown) => { if (mounted) setError('会话树读取失败：' + String(reason)); });
    void load();
    const timer = setInterval(load, 5000);
    return () => { mounted = false; clearInterval(timer); };
  }, [project]);
  if (!project) return <div className="records-page reflect-page"><p className="records-empty">先在左侧选一个项目。</p></div>;
  const roots = (nodes ?? []).filter(node => !node.parent);
  const controllers = roots.filter(node => node.role === 'ideation').concat(roots.filter(node => node.role === 'executor'));
  const loose = roots.filter(node => !controller(node));
  return <div className="records-page reflect-page">
    <div className="records-intro"><h2>Reflect</h2>
      <p>这个项目历来启动过的主控，和它们下面启动的执行主控、worker、审查员、监视器，已结束的也在。worker 上是主控给它那次交付的打分。</p></div>
    {error && <p className="catalog-error" role="alert">{error}</p>}
    <section className="metric-section">
      <h3>主控与会话</h3>
      {!nodes && !error ? <p className="records-empty" role="status">正在读取…</p>
        : nodes && !nodes.length ? <p className="metric-none">这个项目还没有启动过主控或会话。</p>
        : nodes && <>
          <Branch nodes={controllers} all={nodes} level={0} />
          {loose.length > 0 && <div className="reflect-loose"><div className="agent-task-label">未归属</div><Branch nodes={loose} all={nodes} level={0} /></div>}
        </>}
    </section>
    <RetrospectiveSections key={project} project={project} />
  </div>;
}
