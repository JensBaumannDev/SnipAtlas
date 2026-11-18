import { LucideIconData } from '@lucide/angular';
import {
  appWindowIcon,
  arrowRightLeftIcon,
  bugIcon,
  flaskConicalIcon,
  folderIcon,
  listOrderedIcon,
  sparklesIcon,
  terminalIcon,
} from './icons';

const BRAND_LOGOS: Readonly<Partial<Record<string, string>>> = {
  angular: 'angular',
  css: 'css',
  django: 'django',
  docker: 'docker',
  express: 'express',
  fastapi: 'fastapi',
  git: 'git',
  html: 'html5',
  javascript: 'javascript',
  npm: 'npm',
  postgresql: 'postgresql',
  python: 'python',
  react: 'react',
  server: 'linux',
  typescript: 'typescript',
  vue: 'vuedotjs',
};

const TOPIC_ICONS: Readonly<Partial<Record<string, LucideIconData>>> = {
  'django-rest-framework': arrowRightLeftIcon,
  browser: appWindowIcon,
  debugger: bugIcon,
  ki: sparklesIcon,
  terminal: terminalIcon,
  tests: flaskConicalIcon,
  vorgehen: listOrderedIcon,
};

export function topicLogo(slug: string): string | undefined {
  const file = BRAND_LOGOS[slug];
  return file ? `url('img/topics/${file}.svg')` : undefined;
}

export function topicIcon(slug: string): LucideIconData {
  return TOPIC_ICONS[slug] ?? folderIcon;
}
