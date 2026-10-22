import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

// question: an agent waits for the user's answer. quota: a terminal controller's CLI hit its usage limit (T-124).
export type AppNotice = { id: string; kind: 'question' | 'quota'; launch: string; project: string; role: string; task: string | null;
  resets_at?: string | null };
export type QuotaRow = { role_request: string; launch: string; project: string; role_label: string; resets_at: string | null; since: string };
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

  observe(agents: { id: string; state: string; question_id?: string | null; project: string; role_label: string; task: string | null }[],
    quota: QuotaRow[] = []): AppNotice[] {
    const questions = agents.filter(agent => agent.state === 'waiting_user_answer' && agent.question_id);
    this.waiting = questions.length;
    const pending = new Map<string, AppNotice>([
      ...questions.map(agent => [agent.question_id!, { id: agent.question_id!, kind: 'question', launch: agent.id, project: agent.project,
        role: agent.role_label, task: agent.task }] as const),
      // One notice per time a controller runs out; a later run-out after recovery is a new notice.
      ...quota.map(row => [`quota:${row.role_request}:${row.since}`, { id: `quota:${row.role_request}:${row.since}`, kind: 'quota',
        launch: row.launch, project: row.project, role: row.role_label, task: null, resets_at: row.resets_at }] as const)]);
    for (const id of this.active.keys()) if (!pending.has(id)) this.active.delete(id);
    const enabled = this.setting();
    for (const [id, notice] of pending) {
      if (enabled && !this.seen.has(id)) this.active.set(id, notice);
      this.seen.add(id); // Disabled observations must not replay when re-enabled.
    }
    if (!enabled) this.active.clear();
    return [...this.active.values()];
  }

  invalidate(): void { this.active.clear(); this.waiting = 0; }

  badgeCount(): number { return this.setting(undefined, 'dockBadges') ? this.waiting : 0; }
}
