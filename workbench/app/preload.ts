import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('a2a', Object.freeze({
  snapshot: () => ipcRenderer.invoke('a2a:snapshot'),
  output: (offset: number) => ipcRenderer.invoke('a2a:output', offset),
}));
