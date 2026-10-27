import { signal } from '@angular/core';

export class ExpandedSet {
  private readonly slugs = signal<ReadonlySet<string>>(new Set());

  has(slug: string): boolean {
    return this.slugs().has(slug);
  }

  hasAll(slugs: readonly string[]): boolean {
    return slugs.length > 0 && slugs.every((slug) => this.has(slug));
  }

  set(slug: string, expanded: boolean): void {
    this.setAll([slug], expanded);
  }

  setAll(slugs: readonly string[], expanded: boolean): void {
    this.slugs.update((current) => {
      const next = new Set(current);
      slugs.forEach((slug) => (expanded ? next.add(slug) : next.delete(slug)));
      return next;
    });
  }
}
