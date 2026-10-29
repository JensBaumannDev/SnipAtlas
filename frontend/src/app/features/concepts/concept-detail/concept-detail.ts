import { Component, computed, inject, input } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { TranslatePipe } from '@ngx-translate/core';
import { conceptLink } from '../../../core/models/concept';
import { ConceptApi } from '../../../core/api/concept-api';
import { findSubtopic, injectTopic } from '../../../core/content/topic-resource';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { Note } from '../../../shared/note/note';
import { RelatedList } from '../../../shared/related-list/related-list';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TermText } from '../../../shared/term-text/term-text';
import { TopicHeader } from '../../../shared/topic-header/topic-header';

@Component({
  imports: [CodeBlock, Note, RelatedList, ReportLink, TermText, TopicHeader, TranslatePipe],
  selector: 'app-concept-detail',
  styleUrl: './concept-detail.scss',
  templateUrl: './concept-detail.html',
})
export class ConceptDetail {
  private readonly conceptApi = inject(ConceptApi);

  readonly topic = input.required<string>();
  readonly subtopic = input.required<string>();
  readonly slug = input.required<string>();

  private readonly conceptResource = rxResource({
    params: () => this.slug(),
    stream: ({ params }) => this.conceptApi.getBySlug(params),
  });
  private readonly topicConcepts = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.conceptApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly concept = this.conceptResource.value;
  protected readonly currentTopic = injectTopic(this.topic);

  protected readonly currentSubtopic = computed(() =>
    findSubtopic(this.currentTopic(), this.subtopic()),
  );

  protected readonly related = computed(() =>
    this.topicConcepts
      .value()
      .filter((concept) => concept.subtopic === this.subtopic() && concept.slug !== this.slug())
      .map((concept) => ({ slug: concept.slug, title: concept.title, link: conceptLink(concept) })),
  );
}
