import { contextBridge, ipcRenderer } from 'electron';
import type { EmptyInputDeclaration } from '../src/panes.ts';

const argument = process.argv.find(value => value.startsWith('--a2a-pane-keys='));
const paneKeys: unknown = argument ? JSON.parse(argument.slice('--a2a-pane-keys='.length)) : null;
if (!Array.isArray(paneKeys) || paneKeys.some(key => typeof key !== 'string' || !key) ||
    new Set(paneKeys).size !== paneKeys.length) throw new Error('Invalid pane keys');

const home = process.argv.find(value => value.startsWith('--a2a-home='))?.slice('--a2a-home='.length);
if (!home) throw new Error('Missing home directory');

contextBridge.exposeInMainWorld('a2a', Object.freeze({
  paneKeys: Object.freeze(paneKeys),
  home,
  workBranchPrefix: (prefix?: string) => ipcRenderer.invoke('a2a:work-branch-prefix', prefix),
  executionSettings: (change?: { role: string; model: string; effort: string; fast: boolean }) => ipcRenderer.invoke('a2a:execution-settings', change),
  projects: () => ipcRenderer.invoke('a2a:projects'),
  flow: () => ipcRenderer.invoke('a2a:flow'),
  sidebar: () => ipcRenderer.invoke('a2a:sidebar'),
  selectAgent: (launch: string) => ipcRenderer.invoke('a2a:select-agent', launch),
  decideRoleRequest: (roleRequest: string, approved: boolean, parentLaunch?: string | null) => ipcRenderer.invoke('a2a:decide-role-request', roleRequest, approved, parentLaunch ?? null),
  notificationSetting: (enabled?: boolean, preference?: 'notifications' | 'dockBadges') => ipcRenderer.invoke('a2a:notification-setting', enabled, preference),
  tasks: (project: string) => ipcRenderer.invoke('a2a:tasks', project),
  issues: (project: string) => ipcRenderer.invoke('a2a:issues', project),
  restartReview: (task: string, attempt: string, reviewId: string) => ipcRenderer.invoke('a2a:review-restart', task, attempt, reviewId),
  reclaim: (task: string, attempt: string) => ipcRenderer.invoke('a2a:reclaim', task, attempt),
  hideSessions: (launches: string[]) => ipcRenderer.invoke('a2a:hide-sessions', launches),
  answerIssue: (task: string, issue: string, answer: string) => ipcRenderer.invoke('a2a:issue-answer', task, issue, answer),
  disposeIssue: (task: string, issue: string, action: 'close' | 'snooze', reason?: string, basis?: string) =>
    ipcRenderer.invoke('a2a:issue-dispose', task, issue, action, reason, basis),
  records: (project: string) => ipcRenderer.invoke('a2a:records', project),
  receipts: (project: string) => ipcRenderer.invoke('a2a:receipts', project),
  metrics: (project: string, since: string | null, until: string | null) => ipcRenderer.invoke('a2a:metrics', project, since, until),
  archiveUsage: () => ipcRenderer.invoke('a2a:archive-usage'),
  reflect: (project: string) => ipcRenderer.invoke('a2a:reflect', project),
  retrospectives: (project: string) => ipcRenderer.invoke('a2a:retrospectives', project),
  startRetrospective: (project: string, selection: { cli: string; model: string; effort: string }) => ipcRenderer.invoke('a2a:retrospective-start', project, selection),
  saveRetrospectiveSchedule: (change: Record<string, unknown>) => ipcRenderer.invoke('a2a:retrospective-schedule', change),
  decideRetrospectiveSuggestion: (suggestion: string, approved: boolean) => ipcRenderer.invoke('a2a:retrospective-decide', suggestion, approved),
  selection: () => ipcRenderer.invoke('a2a:selection'),
  openProject: () => ipcRenderer.invoke('a2a:open-project'),
  projectSettings: (project: string, directories?: string[]) => ipcRenderer.invoke('a2a:project-settings', project, directories),
  pickExtraDirectory: () => ipcRenderer.invoke('a2a:pick-extra-directory'),
  removeProject: (project: string, attempts?: 'keep' | 'reclaim') => ipcRenderer.invoke('a2a:remove-project', project, attempts),
  selectProject: (project: string | null) => ipcRenderer.invoke('a2a:select-project', project),
  selectTask: (task: string | null) => ipcRenderer.invoke('a2a:select-task', task),
  newTerminal: () => ipcRenderer.invoke('a2a:new-terminal'),
  theme: (theme: 'system' | 'light' | 'dark') => ipcRenderer.invoke('a2a:theme', theme),
  paneAction: (key: string, action: { type: string; direction?: string; name?: string }) => ipcRenderer.invoke('a2a:pane-action', key, action),
  resize: (key: string, cols: number, rows: number) => ipcRenderer.invoke('a2a:resize', key, cols, rows),
  snapshot: (key: string) => ipcRenderer.invoke('a2a:snapshot', key),
  closePane: (key: string) => ipcRenderer.invoke('a2a:close-pane', key),
  output: (key: string, offset: number) => ipcRenderer.invoke('a2a:output', key, offset),
  input: (key: string, data: string, encoding: 'utf8' | 'binary' = 'utf8') => ipcRenderer.invoke('a2a:input', key, data, encoding),
  answer: (key: string, question: string, answers: string[]) => ipcRenderer.invoke('a2a:answer', key, question, answers),
  beginComposition: (key: string) => ipcRenderer.invoke('a2a:composition-start', key),
  releaseQueue: (key: string, declaration: EmptyInputDeclaration) => ipcRenderer.invoke('a2a:release-queue', key, declaration),
  observeFocus: (key: string, rawSequence: string) => ipcRenderer.invoke('a2a:focus-observation', key, rawSequence),
}));
