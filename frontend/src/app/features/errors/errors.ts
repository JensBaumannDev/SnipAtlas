import { Component, computed, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import {
  LucideDynamicIcon,
  LucideListTree,
  LucideMessageSquarePlus,
  LucideSearch,
} from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { ErrorApi } from '../../core/error-api';
import { TopicApi } from '../../core/topic-api';
import { topicIcon, topicLogo } from '../../core/topic-logos';
import { AreaHint, AreaIntro } from '../../shared/area-intro/area-intro';
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
  imports: [AreaIntro, ErrorCard, TranslatePipe, LucideDynamicIcon],
  selector: 'app-errors',
  styleUrl: './errors.scss',
  templateUrl: './errors.html',
})
export class Errors {
  private readonly errorApi = inject(ErrorApi);

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

  protected readonly currentTopic = computed(() =>
    this.groups()
      .flatMap((group) => group.topics)
      .find((topic) => topic.slug === this.topic()),
  );
}
