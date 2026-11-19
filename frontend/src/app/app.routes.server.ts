import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  { path: 'mein-projekt/**', renderMode: RenderMode.Client },
  { path: 'profil/**', renderMode: RenderMode.Client },
  { path: 'einstellungen', renderMode: RenderMode.Client },
  { path: 'passwort-zuruecksetzen', renderMode: RenderMode.Client },
  { path: 'konto-aktivieren', renderMode: RenderMode.Client },
  { path: 'email-bestaetigen', renderMode: RenderMode.Client },
  { path: '**', renderMode: RenderMode.Server },
];
