import { Routes } from '@angular/router';

export const MY_PROJECT_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./project-overview/project-overview').then((m) => m.ProjectOverview),
  },
  {
    path: 'neu',
    title: 'pages.myProjectSetup',
    loadComponent: () => import('./project-setup/project-setup').then((m) => m.ProjectSetup),
  },
  {
    path: 'ordnerstruktur',
    title: 'pages.myProjectStructure',
    loadComponent: () =>
      import('./project-structure/project-structure').then((m) => m.ProjectStructure),
  },
  {
    path: ':phase/:step',
    loadComponent: () =>
      import('./project-step-page/project-step-page').then((m) => m.ProjectStepPage),
  },
];
