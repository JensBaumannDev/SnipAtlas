import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { cachedPerLanguage, notFoundAsUndefined } from './api-request';
import { Group, Topic } from './topic';

@Service()
export class TopicApi {
  private readonly http = inject(HttpClient);

  readonly getGroups = cachedPerLanguage(() => this.http.get<Group[]>('/api/groups/'));

  getBySlug(slug: string): Observable<Topic | undefined> {
    return this.http.get<Topic>(`/api/topics/${slug}/`).pipe(notFoundAsUndefined());
  }
}
