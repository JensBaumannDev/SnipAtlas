import { DOCUMENT, Service, effect, inject, signal } from '@angular/core';

export type ProjectKey = 'project' | 'githubUser' | 'repo' | 'domain' | 'serverUser' | 'serverIp';

export type ProjectValueMap = Partial<Record<ProjectKey, string>>;

export interface PlaceholderPart {
  text: string;
  key?: ProjectKey;
}

export const PROJECT_KEYS: readonly ProjectKey[] = [
  'project',
  'githubUser',
  'repo',
  'domain',
  'serverUser',
  'serverIp',
];

const STORAGE_KEY = 'snipatlas-project';
const PLACEHOLDER = /\{\{(\w+)\}\}/g;
const MARKER = /__ph_(\w+?)__/g;

export function isProjectKey(value: string): value is ProjectKey {
  return PROJECT_KEYS.some((key) => key === value);
}

export function placeholderKeys(code: string): ProjectKey[] {
  const keys = [...code.matchAll(PLACEHOLDER)].map(([, key]) => key).filter(isProjectKey);
  return [...new Set(keys)];
}

export function markPlaceholders(code: string): string {
  return code.replace(PLACEHOLDER, (match, key: string) => (isProjectKey(key) ? `__ph_${key}__` : match));
}

export function splitMarkers(text: string): PlaceholderPart[] {
  const parts: PlaceholderPart[] = [];
  let last = 0;
  for (const match of text.matchAll(MARKER)) {
    const key = match[1];
    if (!isProjectKey(key)) {
      continue;
    }
    if (match.index > last) {
      parts.push({ text: text.slice(last, match.index) });
    }
    parts.push({ text: match[0], key });
    last = match.index + match[0].length;
  }
  if (last < text.length) {
    parts.push({ text: text.slice(last) });
  }
  return parts;
}

export function fillPlaceholders(
  code: string,
  values: ProjectValueMap,
  fallback: (key: ProjectKey) => string,
): string {
  return code.replace(PLACEHOLDER, (match, key: string) =>
    isProjectKey(key) ? values[key]?.trim() || fallback(key) : match,
  );
}

@Service()
export class ProjectValues {
  private readonly window = inject(DOCUMENT).defaultView;

  readonly values = signal<ProjectValueMap>(this.read());

  constructor() {
    effect(() => this.write(this.values()));
  }

  set(key: ProjectKey, value: string): void {
    this.values.update((values) => ({ ...values, [key]: value }));
  }

  private read(): ProjectValueMap {
    try {
      const parsed: unknown = JSON.parse(this.window?.localStorage.getItem(STORAGE_KEY) ?? '{}');
      if (!parsed || typeof parsed !== 'object') {
        return {};
      }
      const values: ProjectValueMap = {};
      for (const [key, value] of Object.entries(parsed)) {
        if (isProjectKey(key) && typeof value === 'string') {
          values[key] = value;
        }
      }
      return values;
    } catch {
      return {};
    }
  }

  private write(values: ProjectValueMap): void {
    try {
      this.window?.localStorage.setItem(STORAGE_KEY, JSON.stringify(values));
    } catch {
      return;
    }
  }
}
