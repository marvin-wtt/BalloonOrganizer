import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        component: () => import('pages/IndexPage.vue'),
      },
    ],
  },
  {
    path: '/projects',
    component: () => import('layouts/ProjectLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'projects',
        component: () => import('pages/ProjectSelectionPage.vue'),
      },
      {
        path: 'create',
        name: 'create-project',
        component: () => import('pages/ProjectCreationPage.vue'),
      },
      {
        path: ':projectId/flights',
        name: 'flights',
        component: () => import('pages/FlightPage.vue'),
      },
      {
        name: 'flight',
        path: ':projectId/flights/:flightId',
        component: () => import('pages/FlightPage.vue'),
      },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
