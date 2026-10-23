import { LucideArrowRightLeft, LucideFolder, LucideIcon, LucideTerminal } from '@lucide/angular';

const BRAND_LOGOS: Readonly<Partial<Record<string, string>>> = {
  angular: 'angular',
  css: 'css',
  django: 'django',
  docker: 'docker',
  git: 'git',
  html: 'html5',
  javascript: 'javascript',
  npm: 'npm',
  postgresql: 'postgresql',
  python: 'python',
  server: 'linux',
  typescript: 'typescript',
};

export const TOPIC_ICONS: Readonly<Partial<Record<string, LucideIcon>>> = {
  'django-rest-framework': LucideArrowRightLeft,
  terminal: LucideTerminal,
};

export function topicLogo(slug: string): string | undefined {
  const file = BRAND_LOGOS[slug];
  return file ? `url('/img/topics/${file}.svg')` : undefined;
}

export function topicIcon(slug: string): LucideIcon {
  return TOPIC_ICONS[slug] ?? LucideFolder;
}
