import { Component, DestroyRef, computed, effect, inject, input, signal } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Entry } from '../../core/entry';
import { EntryApi } from '../../core/entry-api';
import { OutlineItem, PageOutline } from '../../core/page-outline';
import { Preferences } from '../../core/preferences';
import { Subtopic } from '../../core/topic';
import { TopicApi } from '../../core/topic-api';
import { DEFAULT_TOPIC_ICON, TOPIC_ICONS, TOPIC_LOGOS } from '../../core/topic-logos';
import { EntryCard } from './entry-card/entry-card';

interface EntrySection {
  subtopic: Subtopic;
  entries: Entry[];
}

@Component({
  imports: [EntryCard, RouterLink, TranslatePipe],
  selector: 'app-commands',
  styleUrl: './commands.scss',
  templateUrl: './commands.html',
})
export class Commands {
  private readonly entryApi = inject(EntryApi);
  private readonly outline = inject(PageOutline);

  readonly topic = input<string>();
  readonly subtopic = input<string>();

  protected readonly os = inject(Preferences).os;
  protected readonly logos = TOPIC_LOGOS;
  protected readonly icons = TOPIC_ICONS;
  protected readonly defaultIcon = DEFAULT_TOPIC_ICON;

  private readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  private readonly entries = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.entryApi.getByTopic(params),
    defaultValue: [],
  });
  private readonly expandedSlugs = signal<ReadonlySet<string>>(new Set());

  protected readonly currentTopic = computed(() =>
    this.groups()
      .flatMap((group) => group.topics)
      .find((topic) => topic.slug === this.topic()),
  );

  protected readonly currentSubtopic = computed(() =>
    this.currentTopic()?.subtopics.find((subtopic) => subtopic.slug === this.subtopic()),
  );

  protected readonly sections = computed<EntrySection[]>(() => {
    const topic = this.currentTopic();
    if (!topic) {
      return [];
    }
    const current = this.currentSubtopic();
    const subtopics = current ? [current] : topic.subtopics;
    return subtopics
      .map((subtopic) => ({
        subtopic,
        entries: this.entries.value().filter((entry) => entry.subtopic === subtopic.slug),
      }))
      .filter((section) => section.entries.length);
  });

  protected readonly visibleEntries = computed(() =>
    this.sections().flatMap((section) => section.entries),
  );

  protected readonly hasOsVariants = computed(() =>
    this.visibleEntries().some((entry) => typeof entry.code !== 'string'),
  );

  protected readonly allExpanded = computed(() => {
    const entries = this.visibleEntries();
    const expanded = this.expandedSlugs();
    return entries.length > 0 && entries.every((entry) => expanded.has(entry.slug));
  });

  private readonly outlineItems = computed<OutlineItem[]>(() =>
    this.currentSubtopic()
      ? this.visibleEntries().map((entry) => ({ id: entry.slug, label: entry.title }))
      : this.sections().map(({ subtopic }) => ({ id: subtopic.slug, label: subtopic.name })),
  );

  constructor() {
    effect(() => this.outline.set(this.outlineItems()));
    inject(DestroyRef).onDestroy(() => this.outline.clear());
  }

  protected isExpanded(slug: string): boolean {
    return this.expandedSlugs().has(slug);
  }

  protected setExpanded(slug: string, expanded: boolean): void {
    this.updateExpanded([slug], expanded);
  }

  protected toggleAll(): void {
    const slugs = this.visibleEntries().map((entry) => entry.slug);
    this.updateExpanded(slugs, !this.allExpanded());
  }

  private updateExpanded(slugs: string[], expanded: boolean): void {
    this.expandedSlugs.update((current) => {
      const next = new Set(current);
      for (const slug of slugs) {
        if (expanded) {
          next.add(slug);
        } else {
          next.delete(slug);
        }
      }
      return next;
    });
  }
}
