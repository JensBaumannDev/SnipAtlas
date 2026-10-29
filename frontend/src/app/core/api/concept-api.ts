import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { cachedPerLanguage, notFoundAsUndefined } from './api-request';
import { ContentIndex, buildIndex } from '../content/content-index';
import { Concept } from '../models/concept';

const URL = '/api/concepts/';

@Service()
export class ConceptApi {
  private readonly http = inject(HttpClient);

  readonly getAll = cachedPerLanguage(() => this.http.get<Concept[]>(URL));

  getByTopic(topic: string): Observable<Concept[]> {
    return this.http.get<Concept[]>(URL, { params: { topic } });
  }

  getBySlug(slug: string): Observable<Concept | undefined> {
    return this.http.get<Concept>(`${URL}${slug}/`).pipe(notFoundAsUndefined());
  }

  getSummary(): Observable<{ entries: number; topics: number }> {
    return this.getAll().pipe(
      map((concepts) => ({
        entries: concepts.length,
        topics: new Set(concepts.map((concept) => concept.topic)).size,
      })),
    );
  }

  getIndex(): Observable<ContentIndex> {
    return this.getAll().pipe(map(buildIndex));
  }
}
