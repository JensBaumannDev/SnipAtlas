import { ViewportScroller } from '@angular/common';
import { Component, ElementRef, Injector, inject, viewChild } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LucideSearch, LucideSettings } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';

const SCROLL_GAP = 16;

@Component({
  imports: [RouterLink, RouterLinkActive, TranslatePipe, LucideSearch, LucideSettings],
  selector: 'app-topbar',
  styleUrl: './topbar.scss',
  templateUrl: './topbar.html',
  host: {
    '(document:keydown)': 'onKeydown($event)',
  },
})
export class Topbar {
  private readonly injector = inject(Injector);
  private readonly searchInput = viewChild.required<ElementRef<HTMLInputElement>>('searchInput');

  constructor() {
    const host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
    inject(ViewportScroller).setOffset(() => [0, host.offsetHeight + SCROLL_GAP]);
  }

  protected async openLogin(): Promise<void> {
    const [{ Dialog }, { Login }] = await Promise.all([
      import('@angular/cdk/dialog'),
      import('../../features/auth/login/login'),
    ]);
    this.injector.get(Dialog).open(Login, {
      ariaLabelledBy: 'login-title',
      autoFocus: '#login-email',
      backdropClass: 'dialog-backdrop',
      disableClose: true,
    });
  }

  protected onKeydown(event: KeyboardEvent): void {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      this.searchInput().nativeElement.focus();
    }
  }
}
