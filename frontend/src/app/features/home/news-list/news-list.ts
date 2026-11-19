import { DatePipe } from '@angular/common';
import { Component, computed, inject, input } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { map } from 'rxjs';
import { TopicApi } from '../../../core/api/topic-api';
import { ContentPaths } from '../../../core/content/content-paths';
import { NewsItem } from '../../../core/models/news';
import { Group } from '../../../core/models/topic';

@Component({
  imports: [DatePipe, RouterLink],
  selector: 'app-news-list',
  styleUrl: './news-list.scss',
  templateUrl: './news-list.html',
})
export class NewsList {
  private readonly paths = inject(ContentPaths);
  private readonly topicNames = toSignal(inject(TopicApi).getGroups().pipe(map(namesBySlug)), {
    initialValue: new Map<string, string>(),
  });

  readonly items = input.required<NewsItem[]>();

  protected readonly rows = computed(() =>
    this.items().map((item) => ({
      ...item,
      topic: this.topicNames().get(item.topic) ?? '',
      link: this.paths.areaLink(item.link),
    })),
  );
}

function namesBySlug(groups: Group[]): Map<string, string> {
  return new Map(groups.flatMap((group) => group.topics).map((topic) => [topic.slug, topic.name]));
}
