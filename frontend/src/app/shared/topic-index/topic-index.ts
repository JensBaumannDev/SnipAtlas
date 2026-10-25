import { Component, computed, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideChevronRight } from '@lucide/angular';
import { AreaContent } from '../../core/area-content';
import { ContentArea, filterGroups } from '../../core/content-index';
import { Subtopic } from '../../core/topic';
import { TopicApi } from '../../core/topic-api';
import { TopicLogo } from '../topic-logo/topic-logo';

@Component({
  imports: [RouterLink, TopicLogo, LucideChevronRight],
  selector: 'app-topic-index',
  styleUrl: './topic-index.scss',
  templateUrl: './topic-index.html',
})
export class TopicIndex {
  private readonly areaContent = inject(AreaContent);

  readonly area = input.required<ContentArea>();
  readonly path = input.required<string>();

  private readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  private readonly index = rxResource({
    params: () => this.area(),
    stream: ({ params }) => this.areaContent.getIndex(params),
  });

  protected readonly visibleGroups = computed(() => {
    const index = this.index.value();
    return index ? filterGroups(this.groups(), index) : [];
  });

  protected subtopicNames(subtopics: Subtopic[]): string {
    return subtopics.map((subtopic) => subtopic.name).join(' · ');
  }
}
