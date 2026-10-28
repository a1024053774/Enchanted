import type { AppNotice } from './notificationCenter.ts';
import './notifications.css';

export function AppNotifications({ notices, nameOf, disabled, onSelect }: {
  notices: AppNotice[]; nameOf: (project: string) => string; disabled: boolean; onSelect: (launch: string) => void;
}) {
  return <aside className="app-notifications" aria-label="工作台通知" aria-live="polite" aria-relevant="additions removals">
    {notices.map(notice => <button key={notice.id} data-notice-id={notice.id} data-notice-kind={notice.kind} data-notice-launch={notice.launch}
      disabled={disabled} onClick={() => onSelect(notice.launch)}>
      {notice.kind === 'quota' ? <>
        <strong>主控额度用完</strong>
        <span>{nameOf(notice.project)} · {notice.role}</span>
        <span>已派出的工作继续 · {notice.resets_at ? `约 ${new Date(notice.resets_at).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })} 恢复` : '恢复时间未知'}</span>
      </> : <>
        <strong>等待用户回答</strong>
        <span>{nameOf(notice.project)} · {notice.role}</span>
        <span>{notice.task ?? '未归属任务'} · 查看问题 →</span>
      </>}
    </button>)}
  </aside>;
}

export function NotificationSettings({ notifications, dockBadges, onChange }: {
  notifications: boolean; dockBadges: boolean;
  onChange: (enabled: boolean, preference: 'notifications' | 'dockBadges') => void;
}) {
  return <fieldset className="notification-settings"><legend>应用内通知</legend>
    <label><input data-notification-setting="notifications" type="checkbox" checked={notifications}
      onChange={event => onChange(event.target.checked, 'notifications')} />等待用户回答或主控额度用完时提醒</label>
    <label><input data-notification-setting="dockBadges" type="checkbox" checked={dockBadges}
      onChange={event => onChange(event.target.checked, 'dockBadges')} />后台时显示 Dock 待答数量</label>
  </fieldset>;
}
