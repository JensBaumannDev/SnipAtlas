import { DOCUMENT, Service, computed, effect, inject } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { storedOption } from '../browser/browser-storage';
import { Session } from '../auth/session';

export type OperatingSystem = 'win' | 'unix';
export type ThemeMode = 'light' | 'dark' | 'system';
export type Language = 'de' | 'en';
export type LanguageMode = Language | 'auto';
export type AccentTheme = 'blue' | 'teal' | 'raspberry' | 'fuchsia';

const DEFAULT_ACCENT: AccentTheme = 'blue';

const OS_KEY = 'snipatlas-os';
const THEME_KEY = 'snipatlas-theme';
const LANGUAGE_KEY = 'snipatlas-language';

@Service()
export class Preferences {
  private readonly document = inject(DOCUMENT);
  private readonly window = this.document.defaultView;
  private readonly translate = inject(TranslateService);
  private readonly session = inject(Session);

  readonly os = storedOption<OperatingSystem>(OS_KEY, ['win', 'unix'], 'win');
  readonly theme = storedOption<ThemeMode>(THEME_KEY, ['light', 'dark', 'system'], 'system');
  readonly languageMode = storedOption<LanguageMode>(LANGUAGE_KEY, ['auto', 'de', 'en'], 'auto');
  readonly language = computed<Language>(() => {
    const mode = this.languageMode();
    return mode === 'auto' ? this.browserLanguage() : mode;
  });
  readonly accent = computed<AccentTheme>(() => this.session.user()?.accent ?? DEFAULT_ACCENT);

  constructor() {
    effect(() => this.applyTheme(this.theme()));
    effect(() => this.applyLanguage(this.language()));
    effect(() => this.applyAccent(this.accent()));
  }

  setLanguage(mode: LanguageMode): void {
    this.languageMode.set(mode);
  }

  setAccent(accent: AccentTheme): void {
    this.session.saveSettings({ accent });
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
  }

  private applyAccent(accent: AccentTheme): void {
    const root = this.document.documentElement;
    if (accent === DEFAULT_ACCENT) {
      root.removeAttribute('data-accent');
    } else {
      root.setAttribute('data-accent', accent);
    }
  }

  private applyLanguage(language: Language): void {
    this.document.documentElement.lang = language;
    this.translate.use(language);
  }

  private browserLanguage(): Language {
    const language = this.window?.navigator.language.toLowerCase() ?? '';
    return language.startsWith('de') ? 'de' : 'en';
  }
}
