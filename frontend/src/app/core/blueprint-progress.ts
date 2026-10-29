import { HttpClient } from '@angular/common/http';
import { Service, effect, inject, untracked } from '@angular/core';
import { Observable } from 'rxjs';
import { Blueprint } from './blueprint';
import { storedJson } from './browser-storage';
import { AuthEvent, Session } from './session';

export type ProgressMap = Readonly<Record<string, readonly string[]>>;

const PROGRESS_KEY = 'snipatlas-progress';
const URL = '/api/me/progress/';

@Service()
export class BlueprintProgress {
  private readonly http = inject(HttpClient);
  private readonly session = inject(Session);

  readonly done = storedJson<ProgressMap>(PROGRESS_KEY, (value) =>
    isProgressMap(value) ? value : {},
  );

  constructor() {
    effect(() => {
      const event = this.session.authEvent();
      untracked(() => this.sync(event));
    });
  }

  doneSteps(blueprint: string): readonly string[] {
    return this.done()[blueprint] ?? [];
  }

  doneCount(blueprint: Blueprint): number {
    const done = this.doneSteps(blueprint.slug);
    return blueprint.steps.filter((step) => done.includes(step.slug)).length;
  }

  toggle(blueprint: string, step: string): void {
    const steps = this.doneSteps(blueprint);
    const active = steps.includes(step);
    const next = active ? steps.filter((slug) => slug !== step) : [...steps, step];
    this.done.update((current) => ({ ...current, [blueprint]: next }));
    const url = `${URL}${blueprint}/${step}/`;
    this.send(active ? this.http.delete<void>(url) : this.http.put<void>(url, null));
  }

  reset(blueprint: string): void {
    this.done.update((current) =>
      Object.fromEntries(Object.entries(current).filter(([slug]) => slug !== blueprint)),
    );
    this.send(this.http.delete<void>(`${URL}${blueprint}/`));
  }

  private sync(event: AuthEvent | undefined): void {
    if (event === 'logout') {
      this.done.set({});
    } else if (event) {
      this.load(event === 'login');
    }
  }

  private load(merge: boolean): void {
    const local = this.done();
    this.http.get<ProgressMap>(URL).subscribe({
      next: (server) => this.done.set(merge ? this.upload(local, server) : server),
      error: () => undefined,
    });
  }

  private upload(local: ProgressMap, server: ProgressMap): ProgressMap {
    const merged: Record<string, readonly string[]> = { ...server };
    for (const [blueprint, steps] of Object.entries(local)) {
      const known = server[blueprint] ?? [];
      const missing = steps.filter((step) => !known.includes(step));
      missing.forEach((step) =>
        this.send(this.http.put<void>(`${URL}${blueprint}/${step}/`, null)),
      );
      merged[blueprint] = [...known, ...missing];
    }
    return merged;
  }

  private send(request: Observable<void>): void {
    if (this.session.user()) {
      request.subscribe({ error: () => undefined });
    }
  }
}

function isProgressMap(value: unknown): value is ProgressMap {
  return (
    typeof value === 'object' &&
    value !== null &&
    !Array.isArray(value) &&
    Object.values(value).every(
      (steps) => Array.isArray(steps) && steps.every((step) => typeof step === 'string'),
    )
  );
}
