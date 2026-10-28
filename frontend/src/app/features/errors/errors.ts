import { Component, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { TranslatePipe } from '@ngx-translate/core';
import { DebugGuideApi } from '../../core/debug-guide-api';
import { ErrorApi } from '../../core/error-api';
import { triangleAlertIcon } from '../../core/icons';
import { syncOutline } from '../../core/page-outline';
import { injectTopic } from '../../core/topic-resource';
import { AreaInfo } from '../../shared/area-info/area-info';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { TopicHeader } from '../../shared/topic-header/topic-header';
import { DebugGuideCard } from './debug-guide-card/debug-guide-card';
import { ErrorCard } from './error-card/error-card';

@Component({
  imports: [AreaInfo, AreaIntro, DebugGuideCard, ErrorCard, TopicHeader, TranslatePipe],
  selector: 'app-errors',
  styleUrl: './errors.scss',
  templateUrl: './errors.html',
})
export class Errors {
  private readonly errorApi = inject(ErrorApi);
  private readonly debugGuideApi = inject(DebugGuideApi);

  readonly topic = input<string>();

  protected readonly icon = triangleAlertIcon;
  protected readonly infoSections = ['message', 'start', 'stuck'];
  protected readonly summary = toSignal(this.errorApi.getSummary(), {
    initialValue: { entries: 0, topics: 0 },
  });

  protected readonly errors = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.errorApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly topicGuides = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.debugGuideApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly currentTopic = injectTopic(this.topic);

  constructor() {
    syncOutline(() =>
      this.currentTopic()
        ? [
            ...this.topicGuides.value().map((guide) => ({ id: guide.slug, label: guide.title })),
            ...this.errors.value().map((error) => ({ id: error.slug, label: error.message })),
          ]
        : [],
    );
  }
}
