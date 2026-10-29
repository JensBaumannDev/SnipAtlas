import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  { path: 'profil/**', renderMode: RenderMode.Client },
  { path: 'einstellungen', renderMode: RenderMode.Client },
  { path: 'passwort-zuruecksetzen', renderMode: RenderMode.Client },
  { path: '**', renderMode: RenderMode.Server },
];
