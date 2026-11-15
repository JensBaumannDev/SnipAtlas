import { Signal, computed } from '@angular/core';
import { ExpandedSet } from '../ui/expanded-set';
import { OutlineItem, syncOutline } from '../ui/page-outline';
import { findSubtopic, groupBySubtopic, injectTopic } from './topic-resource';

interface ListedItem {
  slug: string;
  title: string;
  subtopic: string;
}

export class TopicListing<T extends ListedItem> {
  readonly expanded = new ExpandedSet();
  readonly topic = injectTopic(() => this.topicSlug());
  readonly subtopic = computed(() => findSubtopic(this.topic(), this.subtopicSlug()));

  readonly tabs = computed(() =>
    groupBySubtopic(this.topic()?.subtopics ?? [], this.items()).map((section) => section.subtopic),
  );

  readonly sections = computed(() => {
    const current = this.subtopic();
    const subtopics = current ? [current] : (this.topic()?.subtopics ?? []);
    return groupBySubtopic(subtopics, this.items());
  });

  readonly visible = computed(() => this.sections().flatMap((section) => section.items));
  private readonly visibleSlugs = computed(() => this.visible().map((item) => item.slug));
  readonly allExpanded = computed(() => this.expanded.hasAll(this.visibleSlugs()));

  constructor(
    private readonly topicSlug: Signal<string | undefined>,
    private readonly subtopicSlug: Signal<string | undefined>,
    private readonly items: Signal<T[]>,
  ) {
    syncOutline(() => this.outline());
  }

  toggleAll(): void {
    this.expanded.setAll(this.visibleSlugs(), !this.allExpanded());
  }

  private outline(): OutlineItem[] {
    return this.subtopic()
      ? this.visible().map((item) => ({ id: item.slug, label: item.title }))
      : this.sections().map(({ subtopic }) => ({ id: subtopic.slug, label: subtopic.name }));
  }
}
