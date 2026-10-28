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
import { rxResource, takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import {
  ActivatedRouteSnapshot,
  NavigationEnd,
  PRIMARY_OUTLET,
  Router,
  RouterLink,
  RouterLinkActive,
  UrlSegment,
} from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { filter } from 'rxjs';
import { AreaContent } from '../../core/area-content';
import { ContentArea, filterGroups, isContentArea } from '../../core/content-index';
import { ExpandedSet } from '../../core/expanded-set';
import { chevronDownIcon, chevronRightIcon } from '../../core/icons';
import { activeNavGroup, navGroupSlugs, navGroups } from '../../core/nav-groups';
import { TopicApi } from '../../core/topic-api';
import { Collection } from '../../shared/collection/collection';
import { TopicLogo } from '../../shared/topic-logo/topic-logo';
import { SidebarMode, isSidebarMode } from './sidebar-mode';

const AREA_LABELS: Record<ContentArea, string> = {
  commands: 'nav.commands',
  concepts: 'nav.concepts',
  blueprints: 'nav.blueprints',
  debugging: 'nav.debugging',
};

function deepestData<T>(
  root: ActivatedRouteSnapshot,
  key: string,
  guard: (value: unknown) => value is T,
): T | undefined {
  let found: T | undefined;
  for (let route: ActivatedRouteSnapshot | null = root; route; route = route.firstChild) {
    const value: unknown = route.data[key];
    if (guard(value)) {
      found = value;
    }
  }
  return found;
}

@Component({
  imports: [Collection, RouterLink, RouterLinkActive, TopicLogo, TranslatePipe, LucideDynamicIcon],
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
  private readonly window = inject(DOCUMENT).defaultView;
  private readonly destroyRef = inject(DestroyRef);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly panel = viewChild.required<ElementRef<HTMLElement>>('panel');

  protected readonly chevronDownIcon = chevronDownIcon;
  protected readonly chevronRightIcon = chevronRightIcon;
  protected readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  protected readonly mode = signal<SidebarMode | undefined>(undefined);
  protected readonly basePath = signal('/');
  protected readonly expandedSlug = signal<string | undefined>(undefined);
  protected readonly openGroups = new ExpandedSet();
  protected readonly menuOpen = signal(false);
  protected readonly hasMore = signal(false);

  private readonly activeSlug = signal<string | undefined>(undefined);
  private readonly area = signal<ContentArea | undefined>(undefined);
  private readonly areaContent = inject(AreaContent);
  private readonly index = rxResource({
    params: () => this.area(),
    stream: ({ params }) => this.areaContent.getIndex(params),
  });

  protected readonly areaLabel = computed(() => {
    const area = this.area();
    return area ? AREA_LABELS[area] : undefined;
  });

  private readonly debugWays = rxResource({
    params: () => (this.area() === 'debugging' ? true : undefined),
    stream: () => this.areaContent.getDebugWays(),
    defaultValue: [],
  });

  protected readonly visibleGroups = computed(() => {
    const index = this.index.value();
    if (!index) {
      return [];
    }
    const groups = filterGroups(this.groups(), index);
    return navGroups(this.area(), this.basePath(), groups, this.debugWays.value());
  });

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
    this.observeSize();
  }

  protected toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  protected toggleTopic(slug: string): void {
    this.expandedSlug.update((expanded) => (expanded === slug ? undefined : slug));
  }

  protected updateMore(): void {
    const { scrollHeight, scrollTop, clientHeight } = this.host;
    this.hasMore.set(scrollHeight - scrollTop - clientHeight > 1);
  }

  private observeSize(): void {
    afterNextRender(() => {
      if (!this.window?.ResizeObserver) {
        return;
      }
      const observer = new this.window.ResizeObserver(() => this.updateMore());
      observer.observe(this.host);
      observer.observe(this.panel().nativeElement);
      this.destroyRef.onDestroy(() => observer.disconnect());
    });
  }

  private onNavigation(): void {
    const root = this.router.routerState.snapshot.root;
    const segments = this.urlSegments();
    const mode = deepestData(root, 'sidebar', isSidebarMode);
    const slug = mode ? segments[1]?.path : undefined;
    const area = deepestData(root, 'area', isContentArea);
    this.openGroupsFor(slug, area, area !== this.area());
    this.mode.set(mode);
    this.area.set(area);
    this.basePath.set(`/${segments[0]?.path ?? ''}`);
    this.activeSlug.set(slug);
    this.menuOpen.set(false);
    if (slug) {
      this.expandedSlug.set(slug);
    }
  }

  private urlSegments(): UrlSegment[] {
    return this.router.parseUrl(this.router.url).root.children[PRIMARY_OUTLET]?.segments ?? [];
  }

  private openGroupsFor(
    slug: string | undefined,
    area: ContentArea | undefined,
    areaChanged: boolean,
  ): void {
    if (areaChanged) {
      this.openGroups.replace(navGroupSlugs(area, this.groups()));
      return;
    }
    const active = activeNavGroup(area, slug, this.groups());
    if (active) {
      this.openGroups.set(active, true);
    }
  }
}
