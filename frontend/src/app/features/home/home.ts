import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { TranslatePipe } from '@ngx-translate/core';
import { map } from 'rxjs';
import { NewsApi } from '../../core/api/news-api';
import { SearchBox } from '../../shared/search-box/search-box';
import { AreaCards } from './area-cards/area-cards';
import { GuideLink } from './guide-link/guide-link';
import { NewsList } from './news-list/news-list';

const NEWS_LIMIT = 4;

@Component({
  imports: [AreaCards, GuideLink, NewsList, SearchBox, TranslatePipe],
  selector: 'app-home',
  styleUrl: './home.scss',
  templateUrl: './home.html',
})
export class Home {
  protected readonly news = toSignal(
    inject(NewsApi)
      .getAll()
      .pipe(map((items) => items.slice(0, NEWS_LIMIT))),
    { initialValue: [] },
  );
}
