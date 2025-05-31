import { app, BrowserWindow, ipcMain, type IpcMainEvent } from 'electron';
import type { Project } from 'app/src-common/entities';
import {
  deleteProjectFromPath,
  readProjectFromPath,
  writeProjectToPath,
} from 'app/src-electron/projectsAPI/file-utils';
import path from 'path';
import {
  addProjectMeta,
  getProjectIndex,
  projectFilePath,
  removeProjectMeta,
  updateProjectMeta,
} from 'app/src-electron/projectsAPI/index-store';

export default () => {
  ipcMain.handle('project:index', projectApiHandler.index);
  ipcMain.handle('project:show', projectApiHandler.show);
  ipcMain.handle('project:store', projectApiHandler.store);
  ipcMain.handle('project:update', projectApiHandler.update);
  ipcMain.handle('project:destroy', projectApiHandler.destroy);

  void loadFromArgs(process.argv);

  app.on('open-file', (event, fullFilePath) => {
    void loadExternalFile(fullFilePath);
  });

  app.on('second-instance', (_event, argv) => {
    void loadFromArgs(argv);
  });
};

async function loadFromArgs(args: string[]) {
  if (args.length < 2) {
    return;
  }

  const fullFilePath = args[1];
  if (!fullFilePath) {
    return;
  }

  await loadExternalFile(fullFilePath);
}

async function loadExternalFile(fullFilePath: string) {
  const project = await readProjectFromPath(fullFilePath);

  const conflict = getProjectIndex().find(
    (meta) => meta.id === project.id || meta.filePath === fullFilePath,
  );

  const meta = {
    id: project.id,
    name: project.name,
    description: project.description,
    createdAt: project.createdAt,
    filePath: fullFilePath,
  };

  if (conflict) {
    updateProjectMeta(meta);
  } else {
    addProjectMeta(meta);
  }

  BrowserWindow.getAllWindows().forEach((win) => {
    if (win.isDestroyed()) {
      return;
    }

    if (!win.webContents.isLoading()) {
      win.webContents.on('did-finish-load', () => {
        win.webContents.send('project:request-open', project);
      });
    } else {
      win.webContents.send('project:request-open', project);
    }
  });
}

const handleEvent = (next: (...args: unknown[]) => unknown) => {
  return (_event: IpcMainEvent, ...args: unknown[]) => {
    return next(...args);
  };
};

const projectApiHandler = {
  index: handleEvent(getProjectIndex),
  show: handleEvent(load),
  store: handleEvent(create),
  update: handleEvent(update),
  destroy: handleEvent(remove),
};

async function create(project: Project) {
  const projectDir = app.getPath('userData');
  const fileName = `project-${project.id}.bpp`;
  const fullPath = path.join(projectDir, fileName);

  addProjectMeta({
    ...project,
    filePath: fullPath,
  });

  await writeProjectToPath(project, fullPath);
}

async function load(id: string) {
  const filePath = projectFilePath(id);

  return readProjectFromPath(filePath);
}

async function update(project: Project) {
  const filePath = projectFilePath(project.id);

  await writeProjectToPath(project, filePath);

  updateProjectMeta({
    ...project,
    filePath,
  });
}

async function remove(id: string) {
  const filePath = projectFilePath(id);

  await deleteProjectFromPath(filePath);

  removeProjectMeta(id);
}
