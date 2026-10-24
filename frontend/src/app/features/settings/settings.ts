import { Component, inject, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import {
  AccentTheme,
  LanguageMode,
  OperatingSystem,
  Preferences,
  ThemeMode,
} from '../../core/preferences';
import { Session } from '../../core/session';

interface Option<T> {
  value: T;
  label: string;
}

@Component({
  imports: [TranslatePipe],
  selector: 'app-settings',
  styleUrl: './settings.scss',
  templateUrl: './settings.html',
})
export class Settings {
  readonly embedded = input(false);

  protected readonly preferences = inject(Preferences);
  protected readonly session = inject(Session);

  protected readonly themeOptions: Option<ThemeMode>[] = [
    { value: 'light', label: 'settings.themeLight' },
    { value: 'system', label: 'settings.themeSystem' },
    { value: 'dark', label: 'settings.themeDark' },
  ];

  protected readonly accentOptions: Option<AccentTheme>[] = [
    { value: 'blue', label: 'settings.accentBlue' },
    { value: 'teal', label: 'settings.accentTeal' },
    { value: 'raspberry', label: 'settings.accentRaspberry' },
    { value: 'fuchsia', label: 'settings.accentFuchsia' },
  ];

  protected readonly osOptions: Option<OperatingSystem>[] = [
    { value: 'win', label: 'settings.osWin' },
    { value: 'unix', label: 'settings.osUnix' },
  ];

  protected readonly languageOptions: Option<LanguageMode>[] = [
    { value: 'auto', label: 'settings.languageAuto' },
    { value: 'de', label: 'settings.languageDe' },
    { value: 'en', label: 'settings.languageEn' },
  ];
}
