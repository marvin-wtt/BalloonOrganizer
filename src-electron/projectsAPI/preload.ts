import type { ProjectsAPI } from 'app/src-common/api';
import { ipcRenderer } from 'electron';

const api: ProjectsAPI = {
  index: (...args: unknown[]) => ipcRenderer.invoke('project:index', ...args),
  show: (...args: unknown[]) => ipcRenderer.invoke('project:show', ...args),
  store: (...args: unknown[]) => ipcRenderer.invoke('project:store', ...args),
  update: (...args: unknown[]) => ipcRenderer.invoke('project:update', ...args),
  destroy: (...args: unknown[]) =>
    ipcRenderer.invoke('project:destroy', ...args),
  onOpenRequest: (callback) =>
    ipcRenderer.on('project:request-open', (_event, id) => {
      callback(id);
    }),
};

export default api;
