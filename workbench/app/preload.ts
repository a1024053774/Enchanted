import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('a2a', Object.freeze({
  snapshot: () => ipcRenderer.invoke('a2a:snapshot'),
  output: (offset: number) => ipcRenderer.invoke('a2a:output', offset),
  input: (data: string, encoding: 'utf8' | 'binary' = 'utf8') => ipcRenderer.invoke('a2a:input', data, encoding),
  beginComposition: () => ipcRenderer.invoke('a2a:composition-start'),
  releaseQueue: () => ipcRenderer.invoke('a2a:release-queue'),
  observeFocus: (rawSequence: string) => ipcRenderer.invoke('a2a:focus-observation', rawSequence),
}));
