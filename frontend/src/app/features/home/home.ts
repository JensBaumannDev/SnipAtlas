import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { map } from 'rxjs';
import { NewsApi } from '../../core/news-api';
import { NewsLog } from '../../shared/news-log/news-log';
import { SearchBox } from '../../shared/search-box/search-box';
import { Offer } from './offer/offer';

const NEWS_LIMIT = 4;

@Component({
  imports: [NewsLog, Offer, RouterLink, SearchBox, TranslatePipe],
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
