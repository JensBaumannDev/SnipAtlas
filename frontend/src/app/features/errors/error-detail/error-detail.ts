import { Component, computed, inject, input } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { TranslatePipe } from '@ngx-translate/core';
import { ErrorApi } from '../../../core/api/error-api';
import { errorLink } from '../../../core/models/error-message';
import { injectTopic } from '../../../core/content/topic-resource';
import { RelatedList } from '../../../shared/related-list/related-list';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TopicHeader } from '../../../shared/topic-header/topic-header';
import { ErrorBody } from '../error-body/error-body';

@Component({
  imports: [ErrorBody, RelatedList, ReportLink, TopicHeader, TranslatePipe],
  selector: 'app-error-detail',
  styleUrl: './error-detail.scss',
  templateUrl: './error-detail.html',
})
export class ErrorDetail {
  private readonly errorApi = inject(ErrorApi);

  readonly topic = input.required<string>();
  readonly slug = input.required<string>();

  private readonly errorResource = rxResource({
    params: () => this.slug(),
    stream: ({ params }) => this.errorApi.getBySlug(params),
  });
  private readonly topicErrors = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.errorApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly error = this.errorResource.value;
  protected readonly currentTopic = injectTopic(this.topic);

  protected readonly related = computed(() =>
    this.topicErrors
      .value()
      .filter((error) => error.slug !== this.slug())
      .map((error) => ({ slug: error.slug, title: error.message, link: errorLink(error) })),
  );
}
