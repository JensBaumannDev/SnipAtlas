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
    data: { sidebar: 'subtopics', area: 'commands' },
    loadChildren: () =>
      import('./features/commands/commands.routes').then((m) => m.COMMANDS_ROUTES),
  },
  {
    path: 'grundlagen',
    title: 'pages.concepts',
    data: { sidebar: 'subtopics', area: 'concepts' },
    loadChildren: () =>
      import('./features/concepts/concepts.routes').then((m) => m.CONCEPTS_ROUTES),
  },
  {
    path: 'anleitungen',
    title: 'pages.blueprints',
    data: { sidebar: 'topics', area: 'blueprints' },
    loadChildren: () => import('./features/guides/guides.routes').then((m) => m.GUIDES_ROUTES),
  },
  {
    path: 'fehler',
    title: 'pages.debugging',
    data: { sidebar: 'topics', area: 'debugging' },
    loadChildren: () => import('./features/errors/errors.routes').then((m) => m.ERRORS_ROUTES),
  },
  {
    path: 'begriffe',
    title: 'pages.glossary',
    loadComponent: () => import('./features/glossary/glossary').then((m) => m.Glossary),
  },
  {
    path: 'neu',
    title: 'pages.news',
    loadComponent: () => import('./features/news/news').then((m) => m.News),
  },
  {
    path: 'anfrage',
    title: 'pages.request',
    loadComponent: () => import('./features/request/request').then((m) => m.Request),
  },
  {
    path: 'profil',
    title: 'pages.profile',
    loadChildren: () => import('./features/profile/profile.routes').then((m) => m.PROFILE_ROUTES),
  },
  {
    path: 'einstellungen',
    title: 'pages.settings',
    loadComponent: () => import('./features/settings/settings').then((m) => m.Settings),
  },
  {
    path: 'faq',
    title: 'pages.faq',
    loadComponent: () => import('./features/faq/faq').then((m) => m.Faq),
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
  {
    path: 'passwort-zuruecksetzen',
    title: 'pages.resetPassword',
    loadComponent: () =>
      import('./features/auth/reset-password/reset-password').then((m) => m.ResetPassword),
  },
  {
    path: '**',
    title: 'pages.notFound',
    loadComponent: () => import('./features/not-found/not-found').then((m) => m.NotFound),
  },
];
