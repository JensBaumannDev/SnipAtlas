import { DOCUMENT, Service, effect, inject, signal } from '@angular/core';
import { Blueprint } from './blueprint';

export type ProgressMap = Readonly<Record<string, readonly string[]>>;

const PROGRESS_KEY = 'snipatlas-progress';

@Service()
export class BlueprintProgress {
  private readonly window = inject(DOCUMENT).defaultView;

  readonly done = signal<ProgressMap>(this.read());

  constructor() {
    effect(() => this.write(this.done()));
  }

  doneSteps(blueprint: string): readonly string[] {
    return this.done()[blueprint] ?? [];
  }

  doneCount(blueprint: Blueprint): number {
    const done = this.doneSteps(blueprint.slug);
    return blueprint.steps.filter((step) => done.includes(step.slug)).length;
  }

  toggle(blueprint: string, step: string): void {
    this.done.update((current) => {
      const steps = current[blueprint] ?? [];
      const next = steps.includes(step) ? steps.filter((slug) => slug !== step) : [...steps, step];
      return { ...current, [blueprint]: next };
    });
  }

  reset(blueprint: string): void {
    this.done.update((current) =>
      Object.fromEntries(Object.entries(current).filter(([slug]) => slug !== blueprint)),
    );
  }

  private read(): ProgressMap {
    try {
      const parsed: unknown = JSON.parse(this.window?.localStorage.getItem(PROGRESS_KEY) ?? '{}');
      return isProgressMap(parsed) ? parsed : {};
    } catch {
      return {};
    }
  }

  private write(progress: ProgressMap): void {
    try {
      this.window?.localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
    } catch {
      return;
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
