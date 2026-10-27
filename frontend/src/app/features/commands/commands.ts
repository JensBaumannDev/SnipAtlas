import { Component, computed, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { EntryApi } from '../../core/entry-api';
import { ExpandedSet } from '../../core/expanded-set';
import { terminalIcon } from '../../core/icons';
import { syncOutline } from '../../core/page-outline';
import { Preferences } from '../../core/preferences';
import { findSubtopic, groupBySubtopic, injectTopic } from '../../core/topic-resource';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { TopicHeader } from '../../shared/topic-header/topic-header';
import { TopicIndex } from '../../shared/topic-index/topic-index';
import { EntryCard } from './entry-card/entry-card';

@Component({
  imports: [AreaIntro, EntryCard, RouterLink, TopicHeader, TopicIndex, TranslatePipe],
  selector: 'app-commands',
  styleUrl: './commands.scss',
  templateUrl: './commands.html',
})
export class Commands {
  private readonly entryApi = inject(EntryApi);

  readonly topic = input<string>();
  readonly subtopic = input<string>();

  protected readonly os = inject(Preferences).os;
  protected readonly icon = terminalIcon;
  protected readonly expanded = new ExpandedSet();
  protected readonly summary = toSignal(this.entryApi.getSummary(), {
    initialValue: { entries: 0, topics: 0 },
  });

  private readonly entries = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.entryApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly currentTopic = injectTopic(this.topic);
  protected readonly currentSubtopic = computed(() =>
    findSubtopic(this.currentTopic(), this.subtopic()),
  );

  protected readonly sections = computed(() => {
    const current = this.currentSubtopic();
    const subtopics = current ? [current] : (this.currentTopic()?.subtopics ?? []);
    return groupBySubtopic(subtopics, this.entries.value());
  });

  protected readonly visibleEntries = computed(() =>
    this.sections().flatMap((section) => section.items),
  );
  private readonly visibleSlugs = computed(() => this.visibleEntries().map((entry) => entry.slug));
  protected readonly allExpanded = computed(() => this.expanded.hasAll(this.visibleSlugs()));

  protected readonly hasOsVariants = computed(() =>
    this.visibleEntries().some((entry) => typeof entry.code !== 'string'),
  );

  constructor() {
    syncOutline(() =>
      this.currentSubtopic()
        ? this.visibleEntries().map((entry) => ({ id: entry.slug, label: entry.title }))
        : this.sections().map(({ subtopic }) => ({ id: subtopic.slug, label: subtopic.name })),
    );
  }

  protected toggleAll(): void {
    this.expanded.setAll(this.visibleSlugs(), !this.allExpanded());
  }
}
