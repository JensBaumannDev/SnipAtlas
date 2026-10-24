import { Component, DestroyRef, computed, effect, inject, input, signal } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideCopy, LucideListTree, LucideSettings } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { Entry } from '../../core/entry';
import { EntryApi } from '../../core/entry-api';
import { OutlineItem, PageOutline } from '../../core/page-outline';
import { Preferences } from '../../core/preferences';
import { Subtopic } from '../../core/topic';
import { TopicApi } from '../../core/topic-api';
import { AreaHint, AreaIntro } from '../../shared/area-intro/area-intro';
import { TopicHeader } from '../../shared/topic-header/topic-header';
import { EntryCard } from './entry-card/entry-card';

const HINTS: AreaHint[] = [
  {
    icon: LucideListTree,
    title: 'commands.hints.choose.title',
    text: 'commands.hints.choose.text',
  },
  { icon: LucideCopy, title: 'commands.hints.copy.title', text: 'commands.hints.copy.text' },
  {
    icon: LucideSettings,
    title: 'commands.hints.os.title',
    text: 'commands.hints.os.text',
    link: { label: 'commands.hints.osLink', path: '/einstellungen' },
  },
];

interface EntrySection {
  subtopic: Subtopic;
  entries: Entry[];
}

@Component({
  imports: [AreaIntro, EntryCard, RouterLink, TopicHeader, TranslatePipe],
  selector: 'app-commands',
  styleUrl: './commands.scss',
  templateUrl: './commands.html',
})
export class Commands {
  private readonly entryApi = inject(EntryApi);
  private readonly outline = inject(PageOutline);
  private readonly topicApi = inject(TopicApi);

  readonly topic = input<string>();
  readonly subtopic = input<string>();

  protected readonly os = inject(Preferences).os;

  protected readonly hints = HINTS;
  protected readonly summary = toSignal(this.entryApi.getSummary(), {
    initialValue: { entries: 0, topics: 0 },
  });

  private readonly entries = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.entryApi.getByTopic(params),
    defaultValue: [],
  });
  private readonly expandedSlugs = signal<ReadonlySet<string>>(new Set());

  private readonly topicResource = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.topicApi.getBySlug(params),
  });

  protected readonly currentTopic = this.topicResource.value;

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
