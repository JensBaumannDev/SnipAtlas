import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { cachedPerLanguage, notFoundAsUndefined } from './api-request';
import { ContentIndex, buildIndex } from './content-index';
import { Entry } from './entry';

const URL = '/api/entries/';

@Service()
export class EntryApi {
  private readonly http = inject(HttpClient);

  readonly getAll = cachedPerLanguage(() => this.http.get<Entry[]>(URL));

  getByTopic(topic: string): Observable<Entry[]> {
    return this.http.get<Entry[]>(URL, { params: { topic } });
  }

  getBySlug(slug: string): Observable<Entry | undefined> {
    return this.http.get<Entry>(`${URL}${slug}/`).pipe(notFoundAsUndefined());
  }

  getSummary(): Observable<{ entries: number; topics: number }> {
    return this.getAll().pipe(
      map((entries) => ({
        entries: entries.length,
        topics: new Set(entries.map((entry) => entry.topic)).size,
      })),
    );
  }

  getIndex(): Observable<ContentIndex> {
    return this.getAll().pipe(map(buildIndex));
  }
}
