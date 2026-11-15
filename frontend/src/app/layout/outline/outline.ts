import {
  Component,
  DOCUMENT,
  DestroyRef,
  afterNextRender,
  computed,
  inject,
  signal,
} from '@angular/core';
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
    '[style.margin-top.px]': 'stageOffset()',
    '(window:scroll)': 'updateActive()',
  },
})
export class Outline {
  private readonly document = inject(DOCUMENT);
  private readonly destroyRef = inject(DestroyRef);
  private readonly activeId = signal<string | undefined>(undefined);

  protected readonly stageOffset = signal(0);

  protected readonly items = inject(PageOutline).items;

  protected readonly currentId = computed(() => {
    const items = this.items();
    const active = items.find((item) => item.id === this.activeId());
    return active?.id ?? items[0]?.id;
  });

  constructor() {
    afterNextRender(() => this.observeMain());
  }

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

  private observeMain(): void {
    const view = this.document.defaultView;
    const main = this.document.getElementById('main');
    if (!view?.ResizeObserver || !main) {
      return;
    }
    const observer = new view.ResizeObserver(() => this.measureStage(main));
    observer.observe(main);
    this.destroyRef.onDestroy(() => observer.disconnect());
  }

  private measureStage(main: HTMLElement): void {
    const stage = main.querySelector('.stage');
    const bottom = stage
      ? stage.getBoundingClientRect().bottom - main.getBoundingClientRect().top
      : 0;
    this.stageOffset.set(Math.max(0, Math.round(bottom)));
  }

  private isScrolledToEnd(): boolean {
    const view = this.document.defaultView;
    if (!view) {
      return false;
    }
    return view.innerHeight + view.scrollY >= this.document.documentElement.scrollHeight - 1;
  }
}
