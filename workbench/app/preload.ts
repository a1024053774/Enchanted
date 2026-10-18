import { contextBridge, ipcRenderer } from 'electron';
import type { EmptyInputDeclaration } from '../src/panes.ts';

const argument = process.argv.find(value => value.startsWith('--a2a-pane-keys='));
const paneKeys: unknown = argument ? JSON.parse(argument.slice('--a2a-pane-keys='.length)) : null;
if (!Array.isArray(paneKeys) || !paneKeys.length || paneKeys.some(key => typeof key !== 'string' || !key) ||
    new Set(paneKeys).size !== paneKeys.length) throw new Error('Invalid pane keys');

contextBridge.exposeInMainWorld('a2a', Object.freeze({
  paneKeys: Object.freeze(paneKeys),
  snapshot: (key: string) => ipcRenderer.invoke('a2a:snapshot', key),
  closePane: (key: string) => ipcRenderer.invoke('a2a:close-pane', key),
  output: (key: string, offset: number) => ipcRenderer.invoke('a2a:output', key, offset),
  input: (key: string, data: string, encoding: 'utf8' | 'binary' = 'utf8') => ipcRenderer.invoke('a2a:input', key, data, encoding),
  beginComposition: (key: string) => ipcRenderer.invoke('a2a:composition-start', key),
  releaseQueue: (key: string, declaration: EmptyInputDeclaration) => ipcRenderer.invoke('a2a:release-queue', key, declaration),
  observeFocus: (key: string, rawSequence: string) => ipcRenderer.invoke('a2a:focus-observation', key, rawSequence),
}));
