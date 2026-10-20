import type { AppNotice } from './notificationCenter.ts';
import './notifications.css';

export function AppNotifications({ notices, disabled, onSelect }: {
  notices: AppNotice[]; disabled: boolean; onSelect: (launch: string) => void;
}) {
  return <aside className="app-notifications" aria-label="待回答通知" aria-live="polite" aria-relevant="additions removals">
    {notices.map(notice => <button key={notice.id} data-notice-id={notice.id} data-notice-launch={notice.launch}
      disabled={disabled} onClick={() => onSelect(notice.launch)}>
      <strong>等待用户回答</strong>
      <span>{notice.project} · {notice.role}</span>
      <span>{notice.task ?? '未归属任务'} · 查看问题 →</span>
    </button>)}
  </aside>;
}

export function NotificationSettings({ notifications, dockBadges, onChange }: {
  notifications: boolean; dockBadges: boolean;
  onChange: (enabled: boolean, preference: 'notifications' | 'dockBadges') => void;
}) {
  return <fieldset className="notification-settings"><legend>应用内通知</legend>
    <label><input data-notification-setting="notifications" type="checkbox" checked={notifications}
      onChange={event => onChange(event.target.checked, 'notifications')} />等待用户回答时提醒</label>
    <label><input data-notification-setting="dockBadges" type="checkbox" checked={dockBadges}
      onChange={event => onChange(event.target.checked, 'dockBadges')} />后台时显示 Dock 待答数量</label>
  </fieldset>;
}
