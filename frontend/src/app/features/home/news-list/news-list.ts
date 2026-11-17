import { DatePipe } from '@angular/common';
import { Component, computed, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ContentPaths } from '../../../core/content/content-paths';
import { NewsItem } from '../../../core/models/news';

@Component({
  imports: [DatePipe, RouterLink],
  selector: 'app-news-list',
  styleUrl: './news-list.scss',
  templateUrl: './news-list.html',
})
export class NewsList {
  private readonly paths = inject(ContentPaths);

  readonly items = input.required<NewsItem[]>();

  protected readonly rows = computed(() =>
    this.items().map((item) => ({ ...item, link: this.paths.areaLink(item.link) })),
  );
}
