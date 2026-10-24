import { Component, DestroyRef, computed, effect, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import {
  LucideDynamicIcon,
  LucideListTree,
  LucideMessageSquarePlus,
  LucideSearch,
} from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { DebugGuideApi } from '../../core/debug-guide-api';
import { ErrorApi } from '../../core/error-api';
import { OutlineItem, PageOutline } from '../../core/page-outline';
import { TopicApi } from '../../core/topic-api';
import { topicIcon, topicLogo } from '../../core/topic-logos';
import { AreaHint, AreaIntro } from '../../shared/area-intro/area-intro';
import { DebugGuideCard } from './debug-guide-card/debug-guide-card';
import { ErrorCard } from './error-card/error-card';

const HINTS: AreaHint[] = [
  {
    icon: LucideListTree,
    title: 'debugging.hints.choose.title',
    text: 'debugging.hints.choose.text',
  },
  {
    icon: LucideSearch,
    title: 'debugging.hints.solve.title',
    text: 'debugging.hints.solve.text',
  },
  {
    icon: LucideMessageSquarePlus,
    title: 'debugging.hints.request.title',
    text: 'debugging.hints.request.text',
    link: { label: 'debugging.hints.requestLink', path: '/anfrage' },
  },
];

@Component({
  imports: [AreaIntro, DebugGuideCard, ErrorCard, TranslatePipe, LucideDynamicIcon],
  selector: 'app-errors',
  styleUrl: './errors.scss',
  templateUrl: './errors.html',
})
export class Errors {
  private readonly errorApi = inject(ErrorApi);
  private readonly debugGuideApi = inject(DebugGuideApi);

  readonly topic = input<string>();

  protected readonly topicLogo = topicLogo;
  protected readonly topicIcon = topicIcon;
  protected readonly hints = HINTS;
  protected readonly summary = toSignal(this.errorApi.getSummary(), {
    initialValue: { entries: 0, topics: 0 },
  });

  private readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });

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

  protected readonly currentTopic = computed(() =>
    this.groups()
      .flatMap((group) => group.topics)
      .find((topic) => topic.slug === this.topic()),
  );

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
