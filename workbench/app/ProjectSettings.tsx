import { useEffect, useRef, useState } from 'react';

export function ProjectSettings({ project, onClose }: { project: string; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [settings, setSettings] = useState<{ repo: string; extra_directories: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    dialog.current!.showModal();
    let active = true;
    window.a2a.projectSettings(project).then(value => { if (active) setSettings(value); }, reason => { if (active) setError(String(reason)); });
    return () => { active = false; };
  }, [project]);
  const add = async () => {
    setBusy(true); setError(null);
    try {
      const path = await window.a2a.pickExtraDirectory();
      if (path) setSettings(current => current && ({ ...current, extra_directories: [...new Set([...current.extra_directories, path])] }));
    } catch (reason) { setError('目录未添加：' + String(reason)); }
    finally { setBusy(false); }
  };
  const save = async () => {
    setBusy(true); setError(null);
    try { await window.a2a.projectSettings(project, settings!.extra_directories); onClose(); }
    catch (reason) { setError('设置未保存：' + String(reason)); }
    finally { setBusy(false); }
  };
  return <dialog ref={dialog} className="settings-dialog project-settings" aria-labelledby="project-settings-title"
    onClose={onClose} onCancel={event => { event.preventDefault(); if (!busy) onClose(); }}>
    <div className="settings-body">
      <header><h2 id="project-settings-title">编辑项目</h2><button disabled={busy} onClick={onClose} aria-label="关闭编辑项目">关闭</button></header>
      <section><h3>主目录</h3><p className="project-directory">{settings?.repo ?? '正在读取…'}</p></section>
      <section><h3>额外目录</h3>
        <p className="settings-note">新启动的 worker、reviewer 和 monitor 可以写入这些目录。移除后只影响新会话。</p>
        <p className="settings-note">额外目录里的改动不进门禁的审查与集成。worker 交付时须列出改过的额外目录。</p>
        {settings && <ul>{settings.extra_directories.map(path => <li key={path} data-extra-directory={path}>
          <span className="project-directory">{path}</span><button disabled={busy} aria-label={`移除 ${path}`}
            onClick={() => setSettings({ ...settings, extra_directories: settings.extra_directories.filter(value => value !== path) })}>移除</button></li>)}</ul>}
        <button data-project-add disabled={busy || !settings} onClick={() => void add()}>添加目录…</button>
      </section>
      {error && <p role="alert" className="catalog-error">{error}</p>}
      <footer><button disabled={busy} onClick={onClose}>取消</button><button data-project-save disabled={busy || !settings} onClick={() => void save()}>{busy ? '处理中…' : '保存'}</button></footer>
    </div>
  </dialog>;
}

// T-190: removing a project only hides it. Before that the user decides what happens to attempts still open in it.
export function RemoveProjectDialog({ ask, busy, onClose, onChoose }: {
  ask: { project: string; refused: string; details: any }; busy: boolean; onClose: () => void; onChoose: (attempts: 'keep' | 'reclaim') => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => { dialog.current!.showModal(); }, []);
  const attempts: { task: string; state: string }[] = ask.details?.attempts ?? [];
  return <dialog ref={dialog} className="settings-dialog project-settings" aria-labelledby="remove-project-title"
    onClose={onClose} onCancel={event => { event.preventDefault(); if (!busy) onClose(); }}>
    <div className="settings-body">
      <header><h2 id="remove-project-title">移除 {ask.project}</h2><button disabled={busy} onClick={onClose} aria-label="关闭">关闭</button></header>
      {ask.refused === 'project_has_running_terminals' ? <section>
        <p className="settings-note">这个项目还有 {ask.details?.count} 个运行中的终端。先关掉它们再移除。</p>
      </section> : ask.refused === 'project_reclaim_failed' ? <section>
        <p className="settings-note">回收 {ask.details?.task} 没有成功（{ask.details?.error}）。可以保留它直接移除，以后重新打开这个目录再处理。</p>
      </section> : <section>
        <p className="settings-note">移除只是从列表隐藏，任务和记录都留着，重新打开这个目录就回来。下面的任务还有没回收的 attempt：</p>
        <ul>{attempts.map(row => <li key={row.task}><span className="project-directory">{row.task.split('+').slice(1).join('+')}</span> {row.state}</li>)}</ul>
      </section>}
      <footer>
        <button disabled={busy} onClick={onClose}>取消</button>
        {ask.refused !== 'project_has_running_terminals' && <button data-remove-keep disabled={busy} onClick={() => onChoose('keep')}>保留并移除</button>}
        {ask.refused === 'project_has_active_attempts' && <button data-remove-reclaim disabled={busy} onClick={() => onChoose('reclaim')}>回收并移除</button>}
      </footer>
    </div>
  </dialog>;
}
