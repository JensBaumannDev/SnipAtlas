import { Component, DOCUMENT, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { PageOutline } from '../../core/ui/page-outline';

const ACTIVE_OFFSET = 160;

@Component({
  imports: [RouterLink, TranslatePipe],
  selector: 'app-outline',
  styleUrl: './outline.scss',
  templateUrl: './outline.html',
  host: {
    '[hidden]': '!items().length',
    '(window:scroll)': 'updateActive()',
  },
})
export class Outline {
  private readonly document = inject(DOCUMENT);
  private readonly activeId = signal<string | undefined>(undefined);

  protected readonly items = inject(PageOutline).items;

  protected readonly currentId = computed(() => {
    const items = this.items();
    const active = items.find((item) => item.id === this.activeId());
    return active?.id ?? items[0]?.id;
  });

  protected updateActive(): void {
    const items = this.items();
    let active: string | undefined;

    for (const item of items) {
      const top = this.document.getElementById(item.id)?.getBoundingClientRect().top;
      if (top !== undefined && top < ACTIVE_OFFSET) {
        active = item.id;
      }
    }
    if (this.isScrolledToEnd()) {
      active = items.at(-1)?.id;
    }
    this.activeId.set(active);
  }

  private isScrolledToEnd(): boolean {
    const view = this.document.defaultView;
    if (!view) {
      return false;
    }
    return view.innerHeight + view.scrollY >= this.document.documentElement.scrollHeight - 1;
  }
}
