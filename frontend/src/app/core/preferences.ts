import { DOCUMENT, Service, effect, inject, signal } from '@angular/core';

export type OperatingSystem = 'win' | 'unix';
export type ThemeMode = 'light' | 'dark' | 'system';

const OS_KEY = 'snipatlas-os';
const THEME_KEY = 'snipatlas-theme';

@Service()
export class Preferences {
  private readonly document = inject(DOCUMENT);
  private readonly window = this.document.defaultView;

  readonly os = signal<OperatingSystem>(this.read(OS_KEY, ['win', 'unix'], 'win'));
  readonly theme = signal<ThemeMode>(this.read(THEME_KEY, ['light', 'dark', 'system'], 'system'));

  constructor() {
    effect(() => this.applyTheme(this.theme()));
    effect(() => this.write(OS_KEY, this.os()));
  }

  setOs(os: OperatingSystem): void {
    this.os.set(os);
  }

  setTheme(theme: ThemeMode): void {
    this.theme.set(theme);
  }

  private applyTheme(theme: ThemeMode): void {
    const root = this.document.documentElement;
    if (theme === 'system') {
      root.removeAttribute('data-theme');
    } else {
      root.setAttribute('data-theme', theme);
    }
    this.write(THEME_KEY, theme);
  }

  private read<T extends string>(key: string, allowed: readonly T[], fallback: T): T {
    try {
      const value = this.window?.localStorage.getItem(key);
      return allowed.find((option) => option === value) ?? fallback;
    } catch {
      return fallback;
    }
  }

  private write(key: string, value: string): void {
    try {
      this.window?.localStorage.setItem(key, value);
    } catch {
      return;
    }
  }
}
