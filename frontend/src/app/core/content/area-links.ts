import { ContentArea } from './content-index';

export interface AreaLink {
  area: ContentArea;
  path: string;
  label: string;
  lead: string;
  preview: string;
}

export const AREA_LINKS: readonly AreaLink[] = [
  {
    area: 'commands',
    path: '/befehle',
    label: 'nav.commands',
    lead: 'commands.lead',
    preview: '$ git switch -c feat/login\n$ npm run build\n$ docker compose up',
  },
  {
    area: 'concepts',
    path: '/grundlagen',
    label: 'nav.concepts',
    lead: 'concepts.lead',
    preview: 'const count = signal(0);\ncount.update((n) => n + 1);',
  },
  {
    area: 'blueprints',
    path: '/anleitungen',
    label: 'nav.blueprints',
    lead: 'guides.lead',
    preview: '$ ng new frontend\n$ django-admin startproject core',
  },
  {
    area: 'debugging',
    path: '/fehler',
    label: 'nav.debugging',
    lead: 'debugging.lead',
    preview: 'TypeError: Cannot read\nproperties of undefined',
  },
];

export function areaForUrl(url: string): ContentArea | undefined {
  const path = `/${url.split(/[/?#]/)[1] ?? ''}`;
  return AREA_LINKS.find((link) => link.path === path)?.area;
}
