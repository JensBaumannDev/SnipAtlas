import { Service } from '@angular/core';
import { Blueprint } from './blueprint';
import { storedJson } from './browser-storage';

export type ProgressMap = Readonly<Record<string, readonly string[]>>;

const PROGRESS_KEY = 'snipatlas-progress';

@Service()
export class BlueprintProgress {
  readonly done = storedJson<ProgressMap>(PROGRESS_KEY, (value) =>
    isProgressMap(value) ? value : {},
  );

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
