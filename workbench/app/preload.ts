import { contextBridge, ipcRenderer } from 'electron';
import type { EmptyInputDeclaration } from '../src/panes.ts';

const argument = process.argv.find(value => value.startsWith('--a2a-pane-keys='));
const paneKeys: unknown = argument ? JSON.parse(argument.slice('--a2a-pane-keys='.length)) : null;
if (!Array.isArray(paneKeys) || paneKeys.some(key => typeof key !== 'string' || !key) ||
    new Set(paneKeys).size !== paneKeys.length) throw new Error('Invalid pane keys');

contextBridge.exposeInMainWorld('a2a', Object.freeze({
  paneKeys: Object.freeze(paneKeys),
  projects: () => ipcRenderer.invoke('a2a:projects'),
  flow: () => ipcRenderer.invoke('a2a:flow'),
  sidebar: () => ipcRenderer.invoke('a2a:sidebar'),
  selectAgent: (launch: string) => ipcRenderer.invoke('a2a:select-agent', launch),
  notificationSetting: (enabled?: boolean) => ipcRenderer.invoke('a2a:notification-setting', enabled),
  tasks: (project: string) => ipcRenderer.invoke('a2a:tasks', project),
  selection: () => ipcRenderer.invoke('a2a:selection'),
  creationRepository: () => ipcRenderer.invoke('a2a:creation-repository'),
  creationSubmit: (input: { task: string; project: string; title: string; branch: string; card: string }) => ipcRenderer.invoke('a2a:creation-submit', input),
  creationCancel: () => ipcRenderer.invoke('a2a:creation-cancel'),
  selectTask: (task: string | null) => ipcRenderer.invoke('a2a:select-task', task),
  newTerminal: (source?: string) => ipcRenderer.invoke('a2a:new-terminal', source),
  paneAction: (key: string, action: { type: string; direction?: string; name?: string }) => ipcRenderer.invoke('a2a:pane-action', key, action),
  resize: (key: string, cols: number, rows: number) => ipcRenderer.invoke('a2a:resize', key, cols, rows),
  snapshot: (key: string) => ipcRenderer.invoke('a2a:snapshot', key),
  closePane: (key: string) => ipcRenderer.invoke('a2a:close-pane', key),
  output: (key: string, offset: number) => ipcRenderer.invoke('a2a:output', key, offset),
  input: (key: string, data: string, encoding: 'utf8' | 'binary' = 'utf8') => ipcRenderer.invoke('a2a:input', key, data, encoding),
  beginComposition: (key: string) => ipcRenderer.invoke('a2a:composition-start', key),
  releaseQueue: (key: string, declaration: EmptyInputDeclaration) => ipcRenderer.invoke('a2a:release-queue', key, declaration),
  observeFocus: (key: string, rawSequence: string) => ipcRenderer.invoke('a2a:focus-observation', key, rawSequence),
}));
