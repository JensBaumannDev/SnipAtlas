import { inject } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivateFn,
  RedirectCommand,
  ResolveFn,
  Router,
} from '@angular/router';
import { Observable, combineLatest, map } from 'rxjs';
import { AreaContent } from './area-content';
import { ContentIndex, isContentArea } from './content-index';
import { ContentPaths } from './content-paths';

interface PlacedItem {
  topic: string;
  subtopic?: string;
}

type FindBySlug<T> = (slug: string) => Observable<T | undefined>;

export function notFound(): RedirectCommand {
  return new RedirectCommand(inject(Router).parseUrl('/404'), { skipLocationChange: true });
}

function inIndex(index: ContentIndex, topic: string, subtopic: string | null): boolean {
  if (!Object.hasOwn(index, topic)) {
    return false;
  }
  return !subtopic || index[topic].includes(subtopic);
}

function inRouteArea(route: ActivatedRouteSnapshot, topic: string): Observable<boolean> {
  return inject(ContentPaths).belongsTo(topic, route.data['ai'] === true);
}

export const contentExists: CanActivateFn = (route) => {
  const area: unknown = route.data['area'];
  const missing = notFound();
  if (!isContentArea(area)) {
    return missing;
  }
  const topic = route.paramMap.get('topic') ?? '';
  const subtopic = route.paramMap.get('subtopic');
  const index = inject(AreaContent).getIndex(area);
  return combineLatest([index, inRouteArea(route, topic)]).pipe(
    map(([found, inArea]) => (inArea && inIndex(found, topic, subtopic) ? true : missing)),
  );
};

function belongsToRoute(item: PlacedItem | undefined, route: ActivatedRouteSnapshot): boolean {
  const subtopic = route.paramMap.get('subtopic');
  return (
    item?.topic === route.paramMap.get('topic') && (subtopic === null || item.subtopic === subtopic)
  );
}

function findInRoute<T>(
  find: FindBySlug<T>,
  route: ActivatedRouteSnapshot,
): Observable<T | undefined> {
  return find(route.paramMap.get('slug') ?? '');
}

export function itemExists(find: FindBySlug<PlacedItem>): CanActivateFn {
  return (route) => {
    const missing = notFound();
    const inArea = inRouteArea(route, route.paramMap.get('topic') ?? '');
    return combineLatest([findInRoute(find, route), inArea]).pipe(
      map(([item, own]) => (own && belongsToRoute(item, route) ? true : missing)),
    );
  };
}

export function slugExists(find: FindBySlug<unknown>): CanActivateFn {
  return (route) => {
    const missing = notFound();
    return findInRoute(find, route).pipe(map((item) => (item ? true : missing)));
  };
}

export function itemText<T>(
  find: FindBySlug<T>,
  title: (item: T) => string,
  fallback: string,
): ResolveFn<string> {
  return (route) => findInRoute(find, route).pipe(map((item) => (item ? title(item) : fallback)));
}
