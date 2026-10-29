import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { cachedPerLanguage, notFoundAsUndefined } from './api-request';
import { ContentIndex, buildIndex } from '../content/content-index';
import { DebugGuide } from '../models/debug-guide';

const URL = '/api/debug-guides/';

@Service()
export class DebugGuideApi {
  private readonly http = inject(HttpClient);

  readonly getAll = cachedPerLanguage(() => this.http.get<DebugGuide[]>(URL));

  getGeneral(): Observable<DebugGuide[]> {
    return this.http.get<DebugGuide[]>(URL, { params: { general: true } });
  }

  getWay(slug: string): Observable<DebugGuide | undefined> {
    return this.http.get<DebugGuide>(`${URL}${slug}/`).pipe(
      notFoundAsUndefined(),
      map((guide) => (guide?.topic ? undefined : guide)),
    );
  }

  getByTopic(topic: string): Observable<DebugGuide[]> {
    return this.http.get<DebugGuide[]>(URL, { params: { topic } });
  }

  getIndex(): Observable<ContentIndex> {
    return this.getAll().pipe(
      map((guides) =>
        buildIndex(guides.flatMap((guide) => (guide.topic ? [{ topic: guide.topic }] : []))),
      ),
    );
  }
}
