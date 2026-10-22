import { DOCUMENT, Service, effect, inject, signal } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

export type OperatingSystem = 'win' | 'unix';
export type ThemeMode = 'light' | 'dark' | 'system';
export type Language = 'de' | 'en';

const OS_KEY = 'snipatlas-os';
const THEME_KEY = 'snipatlas-theme';
const LANGUAGE_KEY = 'snipatlas-language';

@Service()
export class Preferences {
  private readonly document = inject(DOCUMENT);
  private readonly window = this.document.defaultView;
  private readonly translate = inject(TranslateService);

  readonly os = signal<OperatingSystem>(this.read(OS_KEY, ['win', 'unix'], 'win'));
  readonly theme = signal<ThemeMode>(this.read(THEME_KEY, ['light', 'dark', 'system'], 'system'));
  readonly language = signal<Language>(this.read(LANGUAGE_KEY, ['de', 'en'], 'de'));

  constructor() {
    effect(() => this.applyTheme(this.theme()));
    effect(() => this.write(OS_KEY, this.os()));
    effect(() => this.applyLanguage(this.language()));
  }

  setLanguage(language: Language): void {
    this.language.set(language);
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

  private applyLanguage(language: Language): void {
    this.document.documentElement.lang = language;
    this.translate.use(language);
    this.write(LANGUAGE_KEY, language);
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
