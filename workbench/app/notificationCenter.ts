import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

export type AppNotice = { id: string; launch: string; project: string; role: string; task: string | null };
export type NotificationPreference = 'notifications' | 'dockBadges';

// Consume the admitted sidebar state. Question trust belongs to T-108, never
// terminal text or a second classifier in the desktop process.
export class NotificationCenter {
  private readonly file: string;
  private readonly seen = new Set<string>();
  private readonly active = new Map<string, AppNotice>();
  private waiting = 0;
  constructor(userData: string) { this.file = join(userData, 'sidebar-settings.json'); }

  setting(enabled?: boolean, preference: NotificationPreference = 'notifications'): boolean {
    const settings = existsSync(this.file) ? JSON.parse(readFileSync(this.file, 'utf8')) : {};
    if (enabled !== undefined) {
      settings[preference] = enabled;
      writeFileSync(this.file, JSON.stringify(settings) + '\n', { mode: 0o600 });
      if (preference === 'notifications' && !enabled) this.active.clear();
    }
    return settings[preference] === undefined ? true : settings[preference] === true;
  }

  observe(agents: { id: string; state: string; question_id?: string | null; project: string; role_label: string; task: string | null }[]): AppNotice[] {
    const pending = new Map(agents.filter(agent => agent.state === 'waiting_user_answer' && agent.question_id)
      .map(agent => [agent.question_id!, agent]));
    this.waiting = pending.size;
    for (const id of this.active.keys()) if (!pending.has(id)) this.active.delete(id);
    const enabled = this.setting();
    for (const [id, agent] of pending) {
      if (enabled && !this.seen.has(id)) this.active.set(id, { id, launch: agent.id, project: agent.project, role: agent.role_label, task: agent.task });
      this.seen.add(id); // Disabled observations must not replay when re-enabled.
    }
    if (!enabled) this.active.clear();
    return [...this.active.values()];
  }

  badgeCount(): number { return this.setting(undefined, 'dockBadges') ? this.waiting : 0; }
}
