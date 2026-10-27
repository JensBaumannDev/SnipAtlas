import { Component, computed, inject, input } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { ConceptApi } from '../../../core/concept-api';
import { TopicApi } from '../../../core/topic-api';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TermText } from '../../../shared/term-text/term-text';
import { TopicHeader } from '../../../shared/topic-header/topic-header';

@Component({
  imports: [CodeBlock, ReportLink, RouterLink, TermText, TopicHeader, TranslatePipe],
  selector: 'app-concept-detail',
  styleUrl: './concept-detail.scss',
  templateUrl: './concept-detail.html',
})
export class ConceptDetail {
  private readonly conceptApi = inject(ConceptApi);
  private readonly topicApi = inject(TopicApi);

  readonly topic = input.required<string>();
  readonly subtopic = input.required<string>();
  readonly slug = input.required<string>();

  private readonly conceptResource = rxResource({
    params: () => this.slug(),
    stream: ({ params }) => this.conceptApi.getBySlug(params),
  });
  private readonly topicResource = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.topicApi.getBySlug(params),
  });
  private readonly topicConcepts = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.conceptApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly concept = this.conceptResource.value;
  protected readonly currentTopic = this.topicResource.value;

  protected readonly currentSubtopic = computed(() =>
    this.currentTopic()?.subtopics.find((subtopic) => subtopic.slug === this.subtopic()),
  );

  protected readonly related = computed(() =>
    this.topicConcepts
      .value()
      .filter((concept) => concept.subtopic === this.subtopic() && concept.slug !== this.slug()),
  );
}
