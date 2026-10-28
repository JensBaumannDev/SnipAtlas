import { Service } from '@angular/core';
import { storedJson } from './browser-storage';
import { pushText } from './text-parts';

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

function isProjectKey(value: string): value is ProjectKey {
  return PROJECT_KEYS.some((key) => key === value);
}

export function placeholderKeys(code: string): ProjectKey[] {
  const keys = [...code.matchAll(PLACEHOLDER)].map(([, key]) => key).filter(isProjectKey);
  return [...new Set(keys)];
}

export function markPlaceholders(code: string): string {
  return code.replace(PLACEHOLDER, (match, key: string) =>
    isProjectKey(key) ? `__ph_${key}__` : match,
  );
}

export function splitMarkers(text: string): PlaceholderPart[] {
  const parts: PlaceholderPart[] = [];
  let last = 0;
  for (const match of text.matchAll(MARKER)) {
    const key = match[1];
    if (!isProjectKey(key)) {
      continue;
    }
    pushText(parts, text.slice(last, match.index));
    parts.push({ text: match[0], key });
    last = match.index + match[0].length;
  }
  pushText(parts, text.slice(last));
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

function toProjectValues(value: unknown): ProjectValueMap {
  if (!value || typeof value !== 'object') {
    return {};
  }
  const entries: [string, unknown][] = Object.entries(value);
  return Object.fromEntries(
    entries.filter(
      (entry): entry is [ProjectKey, string] =>
        isProjectKey(entry[0]) && typeof entry[1] === 'string',
    ),
  );
}

@Service()
export class ProjectValues {
  readonly values = storedJson(STORAGE_KEY, toProjectValues);

  set(key: ProjectKey, value: string): void {
    this.values.update((values) => ({ ...values, [key]: value }));
  }
}
