import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { NewsItem } from './news';

@Service()
export class NewsApi {
  private readonly http = inject(HttpClient);

  getAll(): Observable<NewsItem[]> {
    return this.http.get<NewsItem[]>('/api/news/');
  }
}
