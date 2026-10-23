import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./features/home/home').then((m) => m.Home),
  },
  {
    path: 'befehle',
    title: 'pages.commands',
    data: { sidebar: 'subtopics' },
    loadChildren: () =>
      import('./features/commands/commands.routes').then((m) => m.COMMANDS_ROUTES),
  },
  {
    path: 'konzepte',
    title: 'pages.concepts',
    data: { sidebar: 'subtopics' },
    loadChildren: () =>
      import('./features/concepts/concepts.routes').then((m) => m.CONCEPTS_ROUTES),
  },
  {
    path: 'bauplaene',
    title: 'pages.blueprints',
    loadComponent: () => import('./features/guides/guides').then((m) => m.Guides),
  },
  {
    path: 'debugging',
    title: 'pages.debugging',
    data: { sidebar: 'topics' },
    loadChildren: () => import('./features/errors/errors.routes').then((m) => m.ERRORS_ROUTES),
  },
  {
    path: 'anfrage',
    title: 'pages.request',
    loadComponent: () => import('./features/request/request').then((m) => m.Request),
  },
  {
    path: 'einstellungen',
    title: 'pages.settings',
    loadComponent: () => import('./features/settings/settings').then((m) => m.Settings),
  },
  {
    path: 'impressum',
    title: 'pages.imprint',
    loadComponent: () => import('./features/legal/imprint/imprint').then((m) => m.Imprint),
  },
  {
    path: 'datenschutz',
    title: 'pages.privacy',
    loadComponent: () => import('./features/legal/privacy/privacy').then((m) => m.Privacy),
  },
  { path: '**', redirectTo: 'befehle' },
];
