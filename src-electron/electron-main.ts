import { app, BrowserWindow } from 'electron';
import initAppApiHandler from 'app/src-electron/appAPI/main';
import initWindowApiHandler from 'app/src-electron/windowAPI/main';
import initProjectApiHandler from 'app/src-electron/projectsAPI/main';
import initSolverApiHandler from 'app/src-electron/solverAPI/main';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'node:url';
import log from 'electron-log';

// needed in case process is undefined under Linux
const platform = process.platform || os.platform();
const currentDir = fileURLToPath(new URL('.', import.meta.url));

const singleInstanceLock = app.requestSingleInstanceLock();
let mainWindow: BrowserWindow | null = null;

if (!singleInstanceLock) {
  log.error(
    'Failed to start application: Another instance seems to be already running.',
  );
  app.quit();
} else {
  app.on('second-instance', () => {
    log.info('Application is already running, restoring window.');
    mainWindow?.restore();
    mainWindow?.focus();
  });
}

async function createWindow() {
  /**
   * Initial window options
   */
  mainWindow = new BrowserWindow({
    icon: path.resolve(currentDir, 'icons/icon.png'), // tray icon
    width: 1000,
    height: 600,
    useContentSize: true,
    frame: false,
    webPreferences: {
      sandbox: true,
      contextIsolation: true,
      preload: path.resolve(
        currentDir,
        path.join(
          process.env.QUASAR_ELECTRON_PRELOAD_FOLDER,
          'electron-preload' + process.env.QUASAR_ELECTRON_PRELOAD_EXTENSION,
        ),
      ),
    },
  });

  if (process.env.DEV) {
    await mainWindow.loadURL(process.env.APP_URL);
  } else {
    await mainWindow.loadFile('index.html');
  }

  if (process.env.DEBUGGING) {
    // if on DEV or Production with debug enabled
    mainWindow.webContents.openDevTools();
  } else {
    // we're on production; no access to devtools pls
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow?.webContents.closeDevTools();
    });
  }
}

app
  .whenReady()
  .then(initWindowApiHandler)
  .then(initAppApiHandler)
  .then(initProjectApiHandler)
  .then(initSolverApiHandler)
  .then(createWindow)
  .catch((reason) => {
    console.error(`Failed to start application: ${reason}`);
  });

app.on('window-all-closed', () => {
  if (platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow().catch((reason) => {
      console.error(`Failed to create window: ${reason}`);
    });
  }
});
