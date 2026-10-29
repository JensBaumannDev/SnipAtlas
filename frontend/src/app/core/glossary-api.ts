import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { cachedPerLanguage } from './api-request';
import { GlossaryTerm } from './glossary-term';

@Service()
export class GlossaryApi {
  private readonly http = inject(HttpClient);

  readonly getAll = cachedPerLanguage(() => this.http.get<GlossaryTerm[]>('/api/glossary/'));
}
