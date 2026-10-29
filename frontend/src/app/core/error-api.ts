import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { cachedPerLanguage, notFoundAsUndefined } from './api-request';
import { ContentIndex, buildIndex } from './content-index';
import { ErrorMessage } from './error-message';

const URL = '/api/errors/';

@Service()
export class ErrorApi {
  private readonly http = inject(HttpClient);

  readonly getAll = cachedPerLanguage(() => this.http.get<ErrorMessage[]>(URL));

  getByTopic(topic: string): Observable<ErrorMessage[]> {
    return this.http.get<ErrorMessage[]>(URL, { params: { topic } });
  }

  getBySlug(slug: string): Observable<ErrorMessage | undefined> {
    return this.http.get<ErrorMessage>(`${URL}${slug}/`).pipe(notFoundAsUndefined());
  }

  getSummary(): Observable<{ entries: number; topics: number }> {
    return this.getAll().pipe(
      map((errors) => ({
        entries: errors.length,
        topics: new Set(errors.map((error) => error.topic)).size,
      })),
    );
  }

  getIndex(): Observable<ContentIndex> {
    return this.getAll().pipe(map(buildIndex));
  }
}
