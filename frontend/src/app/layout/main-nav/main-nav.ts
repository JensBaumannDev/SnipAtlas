import { Component, DOCUMENT, ElementRef, inject, signal, viewChild } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { filter } from 'rxjs';
import { AREA_LINKS, NavArea, areaForUrl } from '../../core/content/area-links';
import { chevronDownIcon, menuIcon, routeIcon, xIcon } from '../../core/ui/icons';
import { AreaMenu } from '../area-menu/area-menu';

const OPEN_DELAY = 150;
const CLOSE_DELAY = 300;

@Component({
  imports: [AreaMenu, RouterLink, RouterLinkActive, TranslatePipe, LucideDynamicIcon],
  selector: 'app-main-nav',
  styleUrl: './main-nav.scss',
  templateUrl: './main-nav.html',
  host: {
    '(document:click)': 'onDocumentClick($event)',
    '(keydown.escape)': 'closeAndFocus()',
  },
})
export class MainNav {
  private readonly router = inject(Router);
  private readonly window = inject(DOCUMENT).defaultView;
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly toggle = viewChild.required<ElementRef<HTMLButtonElement>>('toggle');
  private hoverTimer: number | undefined;

  protected readonly links = AREA_LINKS;
  protected readonly chevronDownIcon = chevronDownIcon;
  protected readonly menuIcon = menuIcon;
  protected readonly routeIcon = routeIcon;
  protected readonly xIcon = xIcon;
  protected readonly openArea = signal<NavArea | undefined>(undefined);
  protected readonly menuOpen = signal(false);
  protected readonly activeArea = signal<NavArea | undefined>(undefined);

  constructor() {
    this.router.events
      .pipe(
        filter((event) => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.onNavigation());
  }

  protected toggleArea(area: NavArea): void {
    this.clearHoverTimer();
    this.openArea.update((open) => (open === area ? undefined : area));
  }

  protected toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  protected onPointerEnter(area: NavArea, event: PointerEvent): void {
    if (this.usesHover(event)) {
      this.schedule(() => this.openArea.set(area), this.openArea() ? 0 : OPEN_DELAY);
    }
  }

  protected onPointerLeave(event: PointerEvent): void {
    if (this.usesHover(event)) {
      this.schedule(() => this.openArea.set(undefined), CLOSE_DELAY);
    }
  }

  protected onFocusOut(event: FocusEvent, item: HTMLElement): void {
    if (event.relatedTarget instanceof Node && !item.contains(event.relatedTarget)) {
      this.openArea.set(undefined);
    }
  }

  protected closeAndFocus(): void {
    const area = this.openArea();
    if (area) {
      this.openArea.set(undefined);
      this.host.querySelector<HTMLElement>(`[aria-controls="area-menu-${area}"]`)?.focus();
    } else if (this.menuOpen()) {
      this.menuOpen.set(false);
      this.toggle().nativeElement.focus();
    }
  }

  protected onDocumentClick(event: MouseEvent): void {
    if (!event.composedPath().includes(this.host)) {
      this.openArea.set(undefined);
      this.menuOpen.set(false);
    }
  }

  private usesHover(event: PointerEvent): boolean {
    return event.pointerType === 'mouse' && !this.toggle().nativeElement.checkVisibility();
  }

  private schedule(action: () => void, delay: number): void {
    this.clearHoverTimer();
    this.hoverTimer = this.window?.setTimeout(action, delay);
  }

  private clearHoverTimer(): void {
    this.window?.clearTimeout(this.hoverTimer);
    this.hoverTimer = undefined;
  }

  private onNavigation(): void {
    this.clearHoverTimer();
    this.activeArea.set(areaForUrl(this.router.url));
    this.openArea.set(undefined);
    this.menuOpen.set(false);
  }
}
