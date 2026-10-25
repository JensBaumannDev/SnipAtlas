import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { TranslatePipe } from '@ngx-translate/core';
import { NewsApi } from '../../core/news-api';
import { NewsLog } from '../../shared/news-log/news-log';

@Component({
  imports: [NewsLog, TranslatePipe],
  selector: 'app-news',
  styleUrl: './news.scss',
  templateUrl: './news.html',
})
export class News {
  protected readonly items = toSignal(inject(NewsApi).getAll(), { initialValue: [] });
}
