import {
  siAngular,
  siCss,
  siDjango,
  siDocker,
  siGit,
  siHtml5,
  siJavascript,
  siLinux,
  siNpm,
  siPostgresql,
  siPython,
  siTypescript,
} from 'simple-icons';

export const TOPIC_LOGOS: Readonly<Partial<Record<string, string>>> = {
  angular: siAngular.path,
  css: siCss.path,
  django: siDjango.path,
  docker: siDocker.path,
  git: siGit.path,
  html: siHtml5.path,
  javascript: siJavascript.path,
  npm: siNpm.path,
  postgresql: siPostgresql.path,
  python: siPython.path,
  server: siLinux.path,
  typescript: siTypescript.path,
};

export const TOPIC_ICONS: Readonly<Partial<Record<string, string>>> = {
  'django-rest-framework': 'M4 8h13l-3-3M20 16H7l3 3',
  terminal: 'm4 17 6-5-6-5M12 19h8',
};

export const DEFAULT_TOPIC_ICON = 'M4 6h16M4 12h16M4 18h10';
