import Store from 'electron-store';
import type { ProjectMeta } from 'app/src-common/entities';
import { app } from 'electron';
import path from 'path';

type RawProjectMeta = Omit<ProjectMeta, 'isInternal'>;

const indexStore = new Store<{
  metas: ProjectMeta[];
}>({ name: 'projects-index' }); // → projects-index.json

export function getProjectIndex() {
  return indexStore.get('metas', []);
}

export function projectFilePath(id: string): string {
  const filePath = getProjectIndex().find((meta) => meta.id === id)?.filePath;

  if (!filePath) {
    throw new Error(`Project with id ${id} not found`);
  }

  return filePath;
}

export function addProjectMeta(meta: RawProjectMeta) {
  const metas = getProjectIndex();

  if (metas.findIndex((m) => m.id === meta.id) !== -1) {
    throw new Error(`Project with id ${meta.id} already exists`);
  }
  metas.push(buildMeta(meta));
  indexStore.set('metas', metas);
}

export function updateProjectMeta(meta: RawProjectMeta) {
  const metas = getProjectIndex();

  metas.splice(
    metas.findIndex((m) => m.id === meta.id),
    1,
    buildMeta(meta),
  );

  indexStore.set('metas', metas);
}

export function removeProjectMeta(id: string) {
  const metas = getProjectIndex().filter((m) => m.id !== id);

  indexStore.set('metas', metas);
}

function buildMeta(meta: RawProjectMeta): ProjectMeta {
  return {
    id: meta.id,
    name: meta.name,
    description: meta.description,
    createdAt: meta.createdAt,
    filePath: meta.filePath,
    isInternal: isPathInternal(meta.filePath),
  };
}

function isPathInternal(filePath: string): boolean {
  const userData = app.getPath('userData');
  const normalizedUserData = path.normalize(userData + path.sep);
  const normalizedFile = path.normalize(filePath);

  return normalizedFile.startsWith(normalizedUserData);
}
