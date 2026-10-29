import { Component, computed, inject, input } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { TranslatePipe } from '@ngx-translate/core';
import { entryLink } from '../../../core/models/entry';
import { EntryApi } from '../../../core/api/entry-api';
import { resolveOsCode } from '../../../core/content/os-code';
import { Preferences } from '../../../core/user-data/preferences';
import { findSubtopic, injectTopic } from '../../../core/content/topic-resource';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { RelatedList } from '../../../shared/related-list/related-list';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TermText } from '../../../shared/term-text/term-text';
import { TopicHeader } from '../../../shared/topic-header/topic-header';
import { FavoriteStar } from '../favorite-star/favorite-star';

@Component({
  imports: [CodeBlock, FavoriteStar, RelatedList, ReportLink, TermText, TopicHeader, TranslatePipe],
  selector: 'app-entry-detail',
  styleUrl: './entry-detail.scss',
  templateUrl: './entry-detail.html',
})
export class EntryDetail {
  private readonly entryApi = inject(EntryApi);
  private readonly os = inject(Preferences).os;

  readonly topic = input.required<string>();
  readonly subtopic = input.required<string>();
  readonly slug = input.required<string>();

  private readonly entryResource = rxResource({
    params: () => this.slug(),
    stream: ({ params }) => this.entryApi.getBySlug(params),
  });
  private readonly topicEntries = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.entryApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly entry = this.entryResource.value;
  protected readonly currentTopic = injectTopic(this.topic);

  protected readonly currentSubtopic = computed(() =>
    findSubtopic(this.currentTopic(), this.subtopic()),
  );

  protected readonly resolved = computed(() => {
    const entry = this.entry();
    return entry ? resolveOsCode(entry.code, this.os()) : undefined;
  });

  protected readonly related = computed(() =>
    this.topicEntries
      .value()
      .filter((entry) => entry.subtopic === this.subtopic() && entry.slug !== this.slug())
      .map((entry) => ({ slug: entry.slug, title: entry.title, link: entryLink(entry) })),
  );
}
