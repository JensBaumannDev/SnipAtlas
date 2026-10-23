import {
  Component,
  DOCUMENT,
  DestroyRef,
  ElementRef,
  afterNextRender,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import {
  ActivatedRouteSnapshot,
  NavigationEnd,
  PRIMARY_OUTLET,
  Router,
  RouterLink,
  RouterLinkActive,
} from '@angular/router';
import { LucideChevronDown, LucideChevronRight, LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { filter } from 'rxjs';
import { TopicApi } from '../../core/topic-api';
import { topicIcon, topicLogo } from '../../core/topic-logos';
import { SidebarMode, isSidebarMode } from './sidebar-mode';

@Component({
  imports: [
    RouterLink,
    RouterLinkActive,
    TranslatePipe,
    LucideChevronDown,
    LucideChevronRight,
    LucideDynamicIcon,
  ],
  selector: 'app-sidebar',
  styleUrl: './sidebar.scss',
  templateUrl: './sidebar.html',
  host: {
    '[hidden]': '!mode()',
    '[class.sidebar--more]': 'hasMore()',
    '(scroll)': 'updateMore()',
  },
})
export class Sidebar {
  private readonly router = inject(Router);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly panel = viewChild.required<ElementRef<HTMLElement>>('panel');

  protected readonly topicLogo = topicLogo;
  protected readonly topicIcon = topicIcon;
  protected readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  protected readonly mode = signal<SidebarMode | undefined>(undefined);
  protected readonly basePath = signal('/');
  protected readonly expandedSlug = signal<string | undefined>(undefined);
  protected readonly openGroups = signal<ReadonlySet<string>>(new Set());
  protected readonly menuOpen = signal(false);
  protected readonly hasMore = signal(false);

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

    const window = inject(DOCUMENT).defaultView;
    const destroyRef = inject(DestroyRef);
    afterNextRender(() => {
      if (!window?.ResizeObserver) {
        return;
      }
      const observer = new window.ResizeObserver(() => this.updateMore());
      observer.observe(this.host);
      observer.observe(this.panel().nativeElement);
      destroyRef.onDestroy(() => observer.disconnect());
    });
  }

  protected toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  protected toggleTopic(slug: string): void {
    this.expandedSlug.update((expanded) => (expanded === slug ? undefined : slug));
  }

  protected toggleGroup(slug: string): void {
    this.openGroups.update((open) => {
      const next = new Set(open);
      if (next.has(slug)) {
        next.delete(slug);
      } else {
        next.add(slug);
      }
      return next;
    });
  }

  protected updateMore(): void {
    const { scrollHeight, scrollTop, clientHeight } = this.host;
    this.hasMore.set(scrollHeight - scrollTop - clientHeight > 1);
  }

  private onNavigation(): void {
    const segments =
      this.router.parseUrl(this.router.url).root.children[PRIMARY_OUTLET]?.segments ?? [];
    const mode = this.modeFromRoute(this.router.routerState.snapshot.root);
    const slug = mode ? segments[1]?.path : undefined;
    const entering = !this.mode();
    const group = this.groups().find((item) => item.topics.some((topic) => topic.slug === slug));

    this.mode.set(mode);
    this.basePath.set(`/${segments[0]?.path ?? ''}`);
    this.activeSlug.set(slug);
    this.menuOpen.set(false);
    if (slug) {
      this.expandedSlug.set(slug);
    }
    if (entering) {
      this.openGroups.set(
        new Set(group ? [group.slug] : this.groups().map((item) => item.slug)),
      );
    } else if (group) {
      this.openGroups.update((open) => new Set(open).add(group.slug));
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
