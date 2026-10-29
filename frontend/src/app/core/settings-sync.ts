import { HttpClient } from '@angular/common/http';
import { Service, computed, effect, inject, signal, untracked } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { debounceTime, filter } from 'rxjs';
import { LanguageMode, OperatingSystem, Preferences, ThemeMode } from './preferences';
import { PROJECT_KEYS, ProjectValueMap, ProjectValues } from './project-values';
import { AuthEvent, Session } from './session';

interface UserSettings {
  os: OperatingSystem;
  theme: ThemeMode;
  language: LanguageMode;
  projectValues: ProjectValueMap;
}

type SettingsChanges = Partial<UserSettings>;

const URL = '/api/me/settings/';
const SAVE_DELAY = 500;

@Service()
export class SettingsSync {
  private readonly http = inject(HttpClient);
  private readonly session = inject(Session);
  private readonly preferences = inject(Preferences);
  private readonly project = inject(ProjectValues);

  private readonly server = signal<UserSettings | undefined>(undefined);
  private readonly local = computed<UserSettings>(() => ({
    os: this.preferences.os(),
    theme: this.preferences.theme(),
    language: this.preferences.languageMode(),
    projectValues: this.project.values(),
  }));
  private readonly changes = computed(() => changedSettings(this.server(), this.local()));

  constructor() {
    effect(() => {
      const event = this.session.authEvent();
      untracked(() => this.sync(event));
    });
    toObservable(this.changes)
      .pipe(
        debounceTime(SAVE_DELAY),
        filter((changes) => Object.keys(changes).length > 0),
      )
      .subscribe((changes) => this.save(changes));
  }

  private sync(event: AuthEvent | undefined): void {
    this.server.set(undefined);
    if (event === 'login' || event === 'restore') {
      this.http.get<UserSettings>(URL).subscribe({
        next: (settings) => this.apply(settings, event === 'login'),
        error: () => undefined,
      });
    }
  }

  private apply(settings: UserSettings, merge: boolean): void {
    const values = this.project.values();
    this.preferences.os.set(settings.os);
    this.preferences.theme.set(settings.theme);
    this.preferences.languageMode.set(settings.language);
    this.project.values.set(
      merge ? fillEmpty(settings.projectValues, values) : settings.projectValues,
    );
    this.server.set(settings);
  }

  private save(changes: SettingsChanges): void {
    this.http.patch<UserSettings>(URL, changes).subscribe({
      next: (settings) => this.server.set(settings),
      error: () => undefined,
    });
  }
}

function changedSettings(server: UserSettings | undefined, local: UserSettings): SettingsChanges {
  if (!server) {
    return {};
  }
  const values = changedValues(server.projectValues, local.projectValues);
  const project = Object.keys(values).length > 0 ? { projectValues: values } : {};
  return { ...changedChoices(server, local), ...project };
}

function changedChoices(server: UserSettings, local: UserSettings): SettingsChanges {
  return {
    ...(local.os !== server.os ? { os: local.os } : {}),
    ...(local.theme !== server.theme ? { theme: local.theme } : {}),
    ...(local.language !== server.language ? { language: local.language } : {}),
  };
}

function changedValues(server: ProjectValueMap, local: ProjectValueMap): ProjectValueMap {
  const changed = PROJECT_KEYS.filter((key) => (local[key] ?? '') !== (server[key] ?? ''));
  return Object.fromEntries(changed.map((key) => [key, local[key] ?? '']));
}

function fillEmpty(server: ProjectValueMap, local: ProjectValueMap): ProjectValueMap {
  const filled = PROJECT_KEYS.filter((key) => !server[key] && local[key]);
  return { ...server, ...Object.fromEntries(filled.map((key) => [key, local[key]])) };
}
