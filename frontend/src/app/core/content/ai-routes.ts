import { inject } from '@angular/core';
import { CanActivateFn, Router, Routes } from '@angular/router';
import { combineLatest, map } from 'rxjs';
import { AreaContent } from './area-content';
import { AI_PATH, aiAreaPath } from './area-links';
import { CONTENT_AREAS } from './content-index';
import { notFound } from './content-guard';
import { ContentPaths } from './content-paths';
import { DEBUG_PATH } from '../models/debug-guide';

export const aiTopicStart: CanActivateFn = (route) => {
  const topic = route.paramMap.get('topic') ?? '';
  const router = inject(Router);
  const missing = notFound();
  const ai = inject(ContentPaths).belongsTo(topic, true);
  return combineLatest([inject(AreaContent).getKindIndexes(), ai]).pipe(
    map(([indexes, isAi]) => {
      const kind = CONTENT_AREAS.find((_, i) => Object.hasOwn(indexes[i], topic));
      return isAi && kind ? router.createUrlTree([aiAreaPath(kind), topic]) : missing;
    }),
  );
};

export function aiRoutes(routes: Routes): Routes {
  const own = routes.filter((route) => route.path && !route.path.startsWith(DEBUG_PATH));
  return [{ path: '', pathMatch: 'full', redirectTo: AI_PATH }, ...own];
}
