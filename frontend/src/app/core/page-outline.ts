import { Service, signal } from '@angular/core';

export interface OutlineItem {
  id: string;
  label: string;
}

@Service()
export class PageOutline {
  readonly items = signal<readonly OutlineItem[]>([]);

  set(items: readonly OutlineItem[]): void {
    this.items.set(items);
  }

  clear(): void {
    this.items.set([]);
  }
}
