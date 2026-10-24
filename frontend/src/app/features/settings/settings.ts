import { Component, inject, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { LanguageMode, OperatingSystem, Preferences, ThemeMode } from '../../core/preferences';

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

  protected readonly themeOptions: Option<ThemeMode>[] = [
    { value: 'light', label: 'settings.themeLight' },
    { value: 'system', label: 'settings.themeSystem' },
    { value: 'dark', label: 'settings.themeDark' },
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
