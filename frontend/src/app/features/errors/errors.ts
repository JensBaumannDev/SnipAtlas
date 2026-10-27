import { Component, DestroyRef, computed, effect, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { TranslatePipe } from '@ngx-translate/core';
import { DebugGuideApi } from '../../core/debug-guide-api';
import { ErrorApi } from '../../core/error-api';
import { triangleAlertIcon } from '../../core/icons';
import { OutlineItem, PageOutline } from '../../core/page-outline';
import { TopicApi } from '../../core/topic-api';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { TopicHeader } from '../../shared/topic-header/topic-header';
import { DebugGuideCard } from './debug-guide-card/debug-guide-card';
import { ErrorCard } from './error-card/error-card';

@Component({
  imports: [AreaIntro, DebugGuideCard, ErrorCard, TopicHeader, TranslatePipe],
  selector: 'app-errors',
  styleUrl: './errors.scss',
  templateUrl: './errors.html',
})
export class Errors {
  private readonly errorApi = inject(ErrorApi);
  private readonly debugGuideApi = inject(DebugGuideApi);
  private readonly topicApi = inject(TopicApi);

  readonly topic = input<string>();

  protected readonly icon = triangleAlertIcon;
  protected readonly summary = toSignal(this.errorApi.getSummary(), {
    initialValue: { entries: 0, topics: 0 },
  });

  protected readonly errors = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.errorApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly generalGuides = toSignal(this.debugGuideApi.getGeneral(), {
    initialValue: [],
  });

  protected readonly topicGuides = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.debugGuideApi.getByTopic(params),
    defaultValue: [],
  });

  private readonly topicResource = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.topicApi.getBySlug(params),
  });

  protected readonly currentTopic = this.topicResource.value;

  private readonly outlineItems = computed<OutlineItem[]>(() =>
    this.currentTopic()
      ? [
          ...this.topicGuides.value().map((guide) => ({ id: guide.slug, label: guide.title })),
          ...this.errors.value().map((error) => ({ id: error.slug, label: error.message })),
        ]
      : this.generalGuides().map((guide) => ({ id: guide.slug, label: guide.title })),
  );

  constructor() {
    const outline = inject(PageOutline);
    effect(() => outline.set(this.outlineItems()));
    inject(DestroyRef).onDestroy(() => outline.clear());
  }
}
