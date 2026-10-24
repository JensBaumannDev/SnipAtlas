import { Injector, Service, Type, inject } from '@angular/core';
import { Observable, combineLatest, from, map, switchMap } from 'rxjs';
import { ContentArea, ContentIndex, mergeIndex } from './content-index';

interface IndexSource {
  getIndex(): Observable<ContentIndex>;
}

@Service()
export class AreaContent {
  private readonly injector = inject(Injector);

  getIndex(area: ContentArea): Observable<ContentIndex> {
    switch (area) {
      case 'commands':
        return this.load(() => import('./entry-api').then((m) => m.EntryApi));
      case 'concepts':
        return this.load(() => import('./concept-api').then((m) => m.ConceptApi));
      case 'blueprints':
        return this.load(() => import('./blueprint-api').then((m) => m.BlueprintApi));
      case 'debugging':
        return combineLatest([
          this.load(() => import('./error-api').then((m) => m.ErrorApi)),
          this.load(() => import('./debug-guide-api').then((m) => m.DebugGuideApi)),
        ]).pipe(map((indexes) => mergeIndex(...indexes)));
    }
  }

  private load(source: () => Promise<Type<IndexSource>>): Observable<ContentIndex> {
    return from(source()).pipe(switchMap((type) => this.injector.get(type).getIndex()));
  }
}
