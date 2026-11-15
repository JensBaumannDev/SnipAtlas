import { DatePipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NewsItem } from '../../../core/models/news';

@Component({
  imports: [DatePipe, RouterLink],
  selector: 'app-news-list',
  styleUrl: './news-list.scss',
  templateUrl: './news-list.html',
})
export class NewsList {
  readonly items = input.required<NewsItem[]>();
}
