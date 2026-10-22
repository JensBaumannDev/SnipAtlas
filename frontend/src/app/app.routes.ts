import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'befehle' },
  {
    path: 'befehle',
    title: 'pages.commands',
    loadComponent: () => import('./features/commands/commands').then((m) => m.Commands),
  },
  {
    path: 'konzepte',
    title: 'pages.concepts',
    loadComponent: () => import('./features/glossary/glossary').then((m) => m.Glossary),
  },
  {
    path: 'bauplaene',
    title: 'pages.blueprints',
    loadComponent: () => import('./features/guides/guides').then((m) => m.Guides),
  },
  {
    path: 'debugging',
    title: 'pages.debugging',
    loadComponent: () => import('./features/errors/errors').then((m) => m.Errors),
  },
  {
    path: 'anfrage',
    title: 'pages.request',
    loadComponent: () => import('./features/request/request').then((m) => m.Request),
  },
  { path: '**', redirectTo: 'befehle' },
];
