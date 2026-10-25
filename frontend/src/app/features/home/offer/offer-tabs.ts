import { TerminalLine } from '../../../shared/terminal-window/terminal-window';

export type OfferArea = 'commands' | 'concepts' | 'blueprints' | 'debugging';

export interface OfferTab {
  area: OfferArea;
  link: string;
  window: string;
  cwd: string;
  cursor: boolean;
  lines: TerminalLine[];
}

export const OFFER_TABS: OfferTab[] = [
  {
    area: 'commands',
    link: '/befehle',
    window: 'snipatlas — zsh',
    cwd: '~/projekt',
    cursor: true,
    lines: [
      { kind: 'comment', text: 'home.offer.commands.comment', translate: true },
      { kind: 'command', text: 'git stash' },
      { kind: 'output', text: 'Saved working directory and index state WIP on main' },
      { kind: 'command', text: 'git stash pop' },
      { kind: 'output', text: 'Dropped refs/stash@{0} (3f2a1c9)' },
    ],
  },
  {
    area: 'concepts',
    link: '/grundlagen',
    window: 'counter.ts',
    cwd: '~',
    cursor: false,
    lines: [
      { kind: 'comment', text: 'home.offer.concepts.comment', translate: true },
      { kind: 'code', text: 'const count = signal(0);' },
      { kind: 'code', text: 'const double = computed(() => count() * 2);' },
      { kind: 'code', text: '' },
      { kind: 'code', text: 'count.set(3);' },
      { kind: 'code', text: 'console.log(double()); // 6' },
    ],
  },
  {
    area: 'blueprints',
    link: '/anleitungen',
    window: 'snipatlas — zsh',
    cwd: '~',
    cursor: false,
    lines: [
      { kind: 'command', text: 'snipatlas bauplan django-projekt-anlegen' },
      { kind: 'done', text: 'home.offer.blueprints.step1', translate: true },
      { kind: 'done', text: 'home.offer.blueprints.step2', translate: true },
      { kind: 'done', text: 'home.offer.blueprints.step3', translate: true },
      { kind: 'todo', text: 'home.offer.blueprints.step4', translate: true },
      { kind: 'todo', text: 'home.offer.blueprints.step5', translate: true },
      { kind: 'comment', text: 'home.offer.blueprints.more', translate: true },
    ],
  },
  {
    area: 'debugging',
    link: '/fehler',
    window: 'snipatlas — zsh',
    cwd: '~/projekt',
    cursor: true,
    lines: [
      { kind: 'command', text: 'python manage.py runserver' },
      { kind: 'error', text: 'Error: That port is already in use.' },
      { kind: 'comment', text: 'home.offer.debugging.comment', translate: true },
      { kind: 'command', text: 'python manage.py runserver 8001' },
      { kind: 'success', text: 'Starting development server at http://127.0.0.1:8001/' },
    ],
  },
];
