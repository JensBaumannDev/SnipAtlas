import { ViewportScroller } from '@angular/common';
import { Service, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, Scroll } from '@angular/router';
import { filter } from 'rxjs';

export const KEEP_SCROLL = 'keep-scroll';

@Service()
export class ScrollRestoration {
  private readonly router = inject(Router);
  private readonly scroller = inject(ViewportScroller);

  constructor() {
    this.scroller.setHistoryScrollRestoration('manual');
    this.router.events
      .pipe(
        filter((event) => event instanceof Scroll),
        takeUntilDestroyed(),
      )
      .subscribe((event) => this.restore(event));
  }

  private restore(event: Scroll): void {
    if (event.position) {
      this.scroller.scrollToPosition(event.position, { behavior: 'instant' });
    } else if (!event.anchor && !this.keepsScroll()) {
      this.scroller.scrollToPosition([0, 0]);
    }
  }

  private keepsScroll(): boolean {
    return this.router.lastSuccessfulNavigation()?.extras.info === KEEP_SCROLL;
  }
}
