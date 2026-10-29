import { Injector, Service, Type, inject } from '@angular/core';
import { Observable, combineLatest, from, map, switchMap } from 'rxjs';
import { ContentArea, ContentIndex, mergeIndex } from './content-index';
import { DebugGuide } from '../models/debug-guide';
import { Topic } from '../models/topic';

const loadDebugGuideApi = () => import('../api/debug-guide-api').then((m) => m.DebugGuideApi);

interface IndexSource {
  getIndex(): Observable<ContentIndex>;
}

function toWayTopic(guide: DebugGuide): Topic {
  return {
    slug: guide.slug,
    name: guide.label ?? guide.title,
    color: 'currentColor',
    subtopics: [],
  };
}

@Service()
export class AreaContent {
  private readonly injector = inject(Injector);

  getIndex(area: ContentArea): Observable<ContentIndex> {
    switch (area) {
      case 'commands':
        return this.load(() => import('../api/entry-api').then((m) => m.EntryApi));
      case 'concepts':
        return this.load(() => import('../api/concept-api').then((m) => m.ConceptApi));
      case 'blueprints':
        return this.load(() => import('../api/blueprint-api').then((m) => m.BlueprintApi));
      case 'debugging':
        return combineLatest([
          this.load(() => import('../api/error-api').then((m) => m.ErrorApi)),
          this.load(loadDebugGuideApi),
        ]).pipe(map((indexes) => mergeIndex(...indexes)));
    }
  }

  getDebugWays(): Observable<Topic[]> {
    return from(loadDebugGuideApi()).pipe(
      switchMap((type) => this.injector.get(type).getGeneral()),
      map((guides) => guides.map(toWayTopic)),
    );
  }

  private load(source: () => Promise<Type<IndexSource>>): Observable<ContentIndex> {
    return from(source()).pipe(switchMap((type) => this.injector.get(type).getIndex()));
  }
}
