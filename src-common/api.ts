import type {
  Project,
  ProjectMeta,
  SmartFillOptions,
  SmartFillPayload,
  VehicleGroup,
} from 'app/src-common/entities';
import type {
  UpdateInfo,
  ProgressInfo,
  UpdateDownloadedEvent,
} from 'electron-updater';

export interface ProjectsAPI {
  index: () => Promise<ProjectMeta[]>;
  show: (id: string) => Promise<Project>;
  store: (project: Project) => Promise<void>;
  update: (project: Project) => Promise<void>;
  destroy: (id: string) => Promise<void>;
  onOpenRequest: (callback: (meta: Project) => void) => void;
}

export interface SolverAPI {
  solveFlight: (
    data: SmartFillPayload,
    options?: SmartFillOptions,
  ) => Promise<VehicleGroup[]>;
}

export interface WindowAPI {
  minimize: () => void;
  toggleMaximize: () => void;
  close: () => void;
  openDevTools: () => void;
}

export type AppAPI = {
  getVersion: () => Promise<string>;

  onUpdateInfo: (callback: (data: AppUpdate) => void) => void;
  checkForUpdate: () => void;
  downloadUpdate: () => void;
  cancelUpdate: () => void;
  installUpdate: () => void;
};

export type AppUpdate =
  | CheckingForUpdates
  | UpdateAvailable
  | UpdateNotAvailable
  | UpdateError
  | UpdateDownloadProgress
  | UpdateCanceled
  | UpdateDownloaded;

export interface CheckingForUpdates {
  name: 'checking-for-update';
}

export interface UpdateAvailable {
  name: 'update-available';
  info: UpdateInfo;
}

export interface UpdateNotAvailable {
  name: 'update-not-available';
  info: UpdateInfo;
}

export interface UpdateError {
  name: 'error';
  error: Error;
}

export interface UpdateDownloadProgress {
  name: 'download-progress';
  info: ProgressInfo;
}

export interface UpdateCanceled {
  name: 'update-cancelled';
  info: UpdateInfo;
}

export interface UpdateDownloaded {
  name: 'update-downloaded';
  info: UpdateDownloadedEvent;
}
