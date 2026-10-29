import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { cachedPerLanguage, notFoundAsUndefined } from './api-request';
import { Blueprint } from '../models/blueprint';
import { ContentIndex, buildIndex } from '../content/content-index';

const URL = '/api/blueprints/';

@Service()
export class BlueprintApi {
  private readonly http = inject(HttpClient);

  readonly getAll = cachedPerLanguage(() => this.http.get<Blueprint[]>(URL));

  getBySlug(slug: string): Observable<Blueprint | undefined> {
    return this.http.get<Blueprint>(`${URL}${slug}/`).pipe(notFoundAsUndefined());
  }

  getSummary(): Observable<{ blueprints: number; steps: number }> {
    return this.getAll().pipe(
      map((blueprints) => ({
        blueprints: blueprints.length,
        steps: blueprints.reduce((sum, blueprint) => sum + blueprint.steps.length, 0),
      })),
    );
  }

  getIndex(): Observable<ContentIndex> {
    return this.getAll().pipe(map(buildIndex));
  }
}
