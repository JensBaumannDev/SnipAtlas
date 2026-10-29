import { Component, computed, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { ConceptApi } from '../../core/api/concept-api';
import { ExpandedSet } from '../../core/ui/expanded-set';
import { bookTextIcon } from '../../core/ui/icons';
import { syncOutline } from '../../core/ui/page-outline';
import { findSubtopic, groupBySubtopic, injectTopic } from '../../core/content/topic-resource';
import { AreaInfo } from '../../shared/area-info/area-info';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { TopicHeader } from '../../shared/topic-header/topic-header';
import { ConceptCard } from './concept-card/concept-card';

@Component({
  imports: [AreaInfo, AreaIntro, ConceptCard, RouterLink, TopicHeader, TranslatePipe],
  selector: 'app-concepts',
  styleUrl: './concepts.scss',
  templateUrl: './concepts.html',
})
export class Concepts {
  private readonly conceptApi = inject(ConceptApi);

  readonly topic = input<string>();
  readonly subtopic = input<string>();

  protected readonly icon = bookTextIcon;
  protected readonly infoSections = ['what', 'why', 'difference'];
  protected readonly expanded = new ExpandedSet();
  protected readonly summary = toSignal(this.conceptApi.getSummary(), {
    initialValue: { entries: 0, topics: 0 },
  });

  private readonly concepts = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.conceptApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly currentTopic = injectTopic(this.topic);
  protected readonly currentSubtopic = computed(() =>
    findSubtopic(this.currentTopic(), this.subtopic()),
  );

  protected readonly sections = computed(() => {
    const current = this.currentSubtopic();
    const subtopics = current ? [current] : (this.currentTopic()?.subtopics ?? []);
    return groupBySubtopic(subtopics, this.concepts.value());
  });

  protected readonly visibleConcepts = computed(() =>
    this.sections().flatMap((section) => section.items),
  );
  private readonly visibleSlugs = computed(() =>
    this.visibleConcepts().map((concept) => concept.slug),
  );
  protected readonly allExpanded = computed(() => this.expanded.hasAll(this.visibleSlugs()));

  constructor() {
    syncOutline(() =>
      this.currentSubtopic()
        ? this.visibleConcepts().map((concept) => ({ id: concept.slug, label: concept.title }))
        : this.sections().map(({ subtopic }) => ({ id: subtopic.slug, label: subtopic.name })),
    );
  }

  protected toggleAll(): void {
    this.expanded.setAll(this.visibleSlugs(), !this.allExpanded());
  }
}
