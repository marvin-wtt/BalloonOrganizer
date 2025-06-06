import { ipcRenderer } from 'electron';
import type { AppAPI } from 'app/src-common/api';

const api: AppAPI = {
  getVersion: () => ipcRenderer.invoke('app:getVersion'),

  onUpdateInfo: (callback) =>
    ipcRenderer.on('app:updateInfo', (event, value) => callback(value)),

  checkForUpdate: () => ipcRenderer.send('app:checkForUpdate'),
  downloadUpdate: () => ipcRenderer.send('app:downloadUpdate'),
  cancelUpdate: () => ipcRenderer.send('app:cancelUpdate'),
  installUpdate: () => ipcRenderer.send('app:installUpdate'),
};

export default api;
