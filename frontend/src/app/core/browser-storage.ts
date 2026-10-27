import { DOCUMENT, Service, WritableSignal, effect, inject, signal } from '@angular/core';

@Service()
export class BrowserStorage {
  private readonly window = inject(DOCUMENT).defaultView;

  read(key: string): string | null {
    try {
      return this.window?.localStorage.getItem(key) ?? null;
    } catch {
      return null;
    }
  }

  write(key: string, value: string): void {
    try {
      this.window?.localStorage.setItem(key, value);
    } catch {
      return;
    }
  }
}

function storedSignal<T>(
  key: string,
  parse: (raw: string | null) => T,
  serialize: (value: T) => string,
): WritableSignal<T> {
  const storage = inject(BrowserStorage);
  const value = signal(parse(storage.read(key)));
  effect(() => storage.write(key, serialize(value())));
  return value;
}

export function storedOption<T extends string>(
  key: string,
  allowed: readonly T[],
  fallback: T,
): WritableSignal<T> {
  const parse = (raw: string | null) => allowed.find((option) => option === raw) ?? fallback;
  return storedSignal(key, parse, (value) => value);
}

export function storedJson<T>(key: string, parse: (value: unknown) => T): WritableSignal<T> {
  return storedSignal(
    key,
    (raw) => parse(parseJson(raw)),
    (value) => JSON.stringify(value),
  );
}

function parseJson(raw: string | null): unknown {
  try {
    return raw === null ? undefined : JSON.parse(raw);
  } catch {
    return undefined;
  }
}
