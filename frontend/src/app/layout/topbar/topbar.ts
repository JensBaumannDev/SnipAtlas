import { ViewportScroller } from '@angular/common';
import { Component, ElementRef, Injector, afterNextRender, inject, viewChild } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LucideSettings } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { LoginDialog } from '../../core/login-dialog';
import { Session } from '../../core/session';
import { SearchBox } from '../../shared/search-box/search-box';
import { UserMenu } from '../user-menu/user-menu';

const SCROLL_GAP = 16;

@Component({
  imports: [RouterLink, RouterLinkActive, SearchBox, TranslatePipe, UserMenu, LucideSettings],
  selector: 'app-topbar',
  styleUrl: './topbar.scss',
  templateUrl: './topbar.html',
  host: {
    '(document:keydown)': 'onKeydown($event)',
  },
})
export class Topbar {
  private readonly injector = inject(Injector);
  private readonly loginDialog = inject(LoginDialog);
  private readonly searchBox = viewChild.required(SearchBox);
  private readonly loginButton = viewChild<ElementRef<HTMLButtonElement>>('loginButton');
  private readonly userMenu = viewChild(UserMenu);

  protected readonly session = inject(Session);

  constructor() {
    const host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
    inject(ViewportScroller).setOffset(() => [0, host.offsetHeight + SCROLL_GAP]);
  }

  protected async openLogin(): Promise<void> {
    const dialogRef = await this.loginDialog.open();
    dialogRef.closed.subscribe(() =>
      afterNextRender(() => this.userMenu()?.focus(), { injector: this.injector }),
    );
  }

  protected onLogout(): void {
    afterNextRender(() => this.loginButton()?.nativeElement.focus(), {
      injector: this.injector,
    });
  }

  protected onKeydown(event: KeyboardEvent): void {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      this.searchBox().focus();
    }
  }
}
