import { Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import {
  ActivatedRouteSnapshot,
  NavigationEnd,
  PRIMARY_OUTLET,
  Router,
  RouterLink,
  RouterLinkActive,
} from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { filter } from 'rxjs';
import { TopicApi } from '../../core/topic-api';
import { DEFAULT_TOPIC_ICON, TOPIC_ICONS, TOPIC_LOGOS } from '../../core/topic-logos';
import { SidebarMode, isSidebarMode } from './sidebar-mode';

@Component({
  imports: [RouterLink, RouterLinkActive, TranslatePipe],
  selector: 'app-sidebar',
  styleUrl: './sidebar.scss',
  templateUrl: './sidebar.html',
  host: {
    '[hidden]': '!mode()',
  },
})
export class Sidebar {
  private readonly router = inject(Router);

  protected readonly logos = TOPIC_LOGOS;
  protected readonly icons = TOPIC_ICONS;
  protected readonly defaultIcon = DEFAULT_TOPIC_ICON;
  protected readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  protected readonly mode = signal<SidebarMode | undefined>(undefined);
  protected readonly basePath = signal('/');
  protected readonly expandedSlug = signal<string | undefined>(undefined);
  protected readonly menuOpen = signal(false);

  private readonly activeSlug = signal<string | undefined>(undefined);

  protected readonly activeTopic = computed(() =>
    this.groups()
      .flatMap((group) => group.topics)
      .find((topic) => topic.slug === this.activeSlug()),
  );

  constructor() {
    this.router.events
      .pipe(
        filter((event) => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe(() => this.onNavigation());
  }

  protected toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  protected toggleTopic(slug: string): void {
    this.expandedSlug.update((expanded) => (expanded === slug ? undefined : slug));
  }

  private onNavigation(): void {
    const segments =
      this.router.parseUrl(this.router.url).root.children[PRIMARY_OUTLET]?.segments ?? [];
    const mode = this.modeFromRoute(this.router.routerState.snapshot.root);
    const slug = mode ? segments[1]?.path : undefined;

    this.mode.set(mode);
    this.basePath.set(`/${segments[0]?.path ?? ''}`);
    this.activeSlug.set(slug);
    this.menuOpen.set(false);
    if (slug) {
      this.expandedSlug.set(slug);
    }
  }

  private modeFromRoute(root: ActivatedRouteSnapshot): SidebarMode | undefined {
    let mode: SidebarMode | undefined;
    for (let route: ActivatedRouteSnapshot | null = root; route; route = route.firstChild) {
      const value: unknown = route.data['sidebar'];
      if (isSidebarMode(value)) {
        mode = value;
      }
    }
    return mode;
  }
}
