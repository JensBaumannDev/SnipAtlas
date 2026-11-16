import { Injector, Service, Signal, Type, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { Observable, combineLatest, from, map, switchMap } from 'rxjs';
import { NavArea } from './area-links';
import { CONTENT_AREAS, ContentIndex, mergeIndex } from './content-index';
import { DebugGuide } from '../models/debug-guide';
import { Topic } from '../models/topic';

const loadDebugGuideApi = () => import('../api/debug-guide-api').then((m) => m.DebugGuideApi);

interface IndexSource {
  getIndex(): Observable<ContentIndex>;
}

interface TopicSource {
  getByTopic(topic: string): Observable<unknown>;
}

const TOPIC_SOURCES: readonly (() => Promise<Type<TopicSource>>)[] = [
  () => import('../api/entry-api').then((m) => m.EntryApi),
  () => import('../api/concept-api').then((m) => m.ConceptApi),
  () => import('../api/error-api').then((m) => m.ErrorApi),
  loadDebugGuideApi,
];

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
  private kindIndexes?: Signal<ContentIndex[]>;

  getIndex(area: NavArea): Observable<ContentIndex> {
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
      case 'ai':
        return this.getAiIndex();
    }
  }

  getKindIndexes(): Observable<ContentIndex[]> {
    return combineLatest(CONTENT_AREAS.map((kind) => this.getIndex(kind)));
  }

  kindIndexesSignal(): Signal<ContentIndex[]> {
    this.kindIndexes ??= toSignal(this.getKindIndexes(), {
      initialValue: [],
      injector: this.injector,
    });
    return this.kindIndexes;
  }

  prefetchTopic(topic: string): void {
    for (const source of TOPIC_SOURCES) {
      from(source())
        .pipe(switchMap((type) => this.injector.get(type).getByTopic(topic)))
        .subscribe();
    }
  }

  getDebugWays(): Observable<Topic[]> {
    return from(loadDebugGuideApi()).pipe(
      switchMap((type) => this.injector.get(type).getGeneral()),
      map((guides) => guides.map(toWayTopic)),
    );
  }

  private getAiIndex(): Observable<ContentIndex> {
    return this.getKindIndexes().pipe(map((indexes) => mergeIndex(...indexes)));
  }

  private load(source: () => Promise<Type<IndexSource>>): Observable<ContentIndex> {
    return from(source()).pipe(switchMap((type) => this.injector.get(type).getIndex()));
  }
}
