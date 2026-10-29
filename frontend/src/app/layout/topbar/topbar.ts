import { ViewportScroller } from '@angular/common';
import {
  Component,
  DOCUMENT,
  ElementRef,
  Injector,
  afterNextRender,
  inject,
  viewChild,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { filter, map } from 'rxjs';
import { settingsIcon } from '../../core/ui/icons';
import { LoginDialog } from '../../core/auth/login-dialog';
import { Session } from '../../core/auth/session';
import { SearchBox } from '../../shared/search-box/search-box';
import { UserMenu } from '../user-menu/user-menu';

const SCROLL_GAP = 16;

@Component({
  imports: [RouterLink, RouterLinkActive, SearchBox, TranslatePipe, UserMenu, LucideDynamicIcon],
  selector: 'app-topbar',
  styleUrl: './topbar.scss',
  templateUrl: './topbar.html',
})
export class Topbar {
  private readonly injector = inject(Injector);
  private readonly loginDialog = inject(LoginDialog);
  private readonly router = inject(Router);
  private readonly loginButton = viewChild<ElementRef<HTMLButtonElement>>('loginButton');
  private readonly userMenu = viewChild(UserMenu);

  protected readonly session = inject(Session);
  protected readonly settingsIcon = settingsIcon;
  protected readonly isHome = toSignal(
    this.router.events.pipe(
      filter((event) => event instanceof NavigationEnd),
      map(() => this.router.url.split(/[?#]/)[0] === '/'),
    ),
    { initialValue: inject(DOCUMENT).defaultView?.location.pathname === '/' },
  );

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
}
