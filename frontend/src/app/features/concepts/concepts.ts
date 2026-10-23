import { Component, DestroyRef, computed, effect, inject, input, signal } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { Concept } from '../../core/concept';
import { ConceptApi } from '../../core/concept-api';
import { OutlineItem, PageOutline } from '../../core/page-outline';
import { Subtopic } from '../../core/topic';
import { TopicApi } from '../../core/topic-api';
import { topicIcon, topicLogo } from '../../core/topic-logos';
import { ConceptCard } from './concept-card/concept-card';

interface ConceptSection {
  subtopic: Subtopic;
  concepts: Concept[];
}

@Component({
  imports: [ConceptCard, RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-concepts',
  styleUrl: './concepts.scss',
  templateUrl: './concepts.html',
})
export class Concepts {
  private readonly conceptApi = inject(ConceptApi);
  private readonly outline = inject(PageOutline);

  readonly topic = input<string>();
  readonly subtopic = input<string>();

  protected readonly topicLogo = topicLogo;
  protected readonly topicIcon = topicIcon;

  private readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  private readonly concepts = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.conceptApi.getByTopic(params),
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

  protected readonly sections = computed<ConceptSection[]>(() => {
    const topic = this.currentTopic();
    if (!topic) {
      return [];
    }
    const current = this.currentSubtopic();
    const subtopics = current ? [current] : topic.subtopics;
    return subtopics
      .map((subtopic) => ({
        subtopic,
        concepts: this.concepts.value().filter((concept) => concept.subtopic === subtopic.slug),
      }))
      .filter((section) => section.concepts.length);
  });

  protected readonly visibleConcepts = computed(() =>
    this.sections().flatMap((section) => section.concepts),
  );

  protected readonly allExpanded = computed(() => {
    const concepts = this.visibleConcepts();
    const expanded = this.expandedSlugs();
    return concepts.length > 0 && concepts.every((concept) => expanded.has(concept.slug));
  });

  private readonly outlineItems = computed<OutlineItem[]>(() =>
    this.currentSubtopic()
      ? this.visibleConcepts().map((concept) => ({ id: concept.slug, label: concept.title }))
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
    const slugs = this.visibleConcepts().map((concept) => concept.slug);
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
