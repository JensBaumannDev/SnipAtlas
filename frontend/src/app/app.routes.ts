import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'befehle' },
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
      import('./features/glossary/glossary.routes').then((m) => m.GLOSSARY_ROUTES),
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
  { path: '**', redirectTo: 'befehle' },
];
