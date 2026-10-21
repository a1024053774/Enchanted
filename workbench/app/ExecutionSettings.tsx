import { useEffect, useState } from 'react';
import type { ExecutionRole, ExecutionSelection } from '../src/executionSettings.ts';
import './execution-settings.css';

const labels: Record<ExecutionRole, string> = { worker: 'Worker', reviewer: '审查员', monitor: '监视器', ideation: '构思主控', executor: '执行主控' };
export function ExecutionSettings() {
  const [settings, setSettings] = useState<Record<ExecutionRole, ExecutionSelection> | null>(null);
  const [role, setRole] = useState<ExecutionRole>('worker');
  const [draft, setDraft] = useState<ExecutionSelection | null>(null);
  const [busy, setBusy] = useState(false), [message, setMessage] = useState('');
  useEffect(() => { let live = true;
    window.a2a.executionSettings().then(value => { if (live) { setSettings(value); setDraft(value.worker); } })
      .catch(error => { if (live) setMessage('读取失败：' + String(error)); });
    return () => { live = false; };
  }, []);
  return <form className="execution-settings" aria-label="主控派发的默认模型" onSubmit={event => {
    event.preventDefault(); if (!draft) return;
    setBusy(true); setMessage('');
    window.a2a.executionSettings({ role, ...draft }).then(value => { setSettings(value); setDraft(value[role]); setMessage('已保存，下次启动生效'); })
      .catch(error => setMessage('保存失败：' + String(error))).finally(() => setBusy(false));
  }}>
    <label>角色<select value={role} disabled={busy || !settings} onChange={event => {
      const next = event.target.value as ExecutionRole; setRole(next); setDraft(settings![next]); setMessage('');
    }}>{Object.entries(labels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
    <label>模型<input value={draft?.model ?? ''} required disabled={busy || !draft} onChange={event => setDraft({ ...draft!, model: event.target.value })} /></label>
    <label>思考强度<input value={draft?.effort ?? ''} required disabled={busy || !draft} onChange={event => setDraft({ ...draft!, effort: event.target.value })} /></label>
    <label className="execution-fast"><input type="checkbox" checked={draft?.fast ?? false} disabled={busy || !draft} onChange={event => setDraft({ ...draft!, fast: event.target.checked })} />Fast</label>
    <p>模型名和思考强度按 CLI 的写法填写，例如 gpt-6.1-sol 与 high。</p>
    <button disabled={busy || !draft}>{busy ? '保存中…' : '保存'}</button>
    {message && <p role="status">{message}</p>}
  </form>;
}
