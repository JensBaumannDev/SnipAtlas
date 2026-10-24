import { inject } from '@angular/core';
import { CanActivateFn, RedirectCommand, Router } from '@angular/router';
import { map } from 'rxjs';
import { AreaContent } from './area-content';
import { isContentArea } from './content-index';

export function notFound(): RedirectCommand {
  return new RedirectCommand(inject(Router).parseUrl('/404'), { skipLocationChange: true });
}

export const contentExists: CanActivateFn = (route) => {
  const area: unknown = route.data['area'];
  const topic = route.paramMap.get('topic') ?? '';
  const subtopic = route.paramMap.get('subtopic');
  const missing = notFound();

  if (!isContentArea(area)) {
    return missing;
  }
  return inject(AreaContent)
    .getIndex(area)
    .pipe(
      map((index) => {
        if (!Object.hasOwn(index, topic)) {
          return missing;
        }
        return !subtopic || index[topic].includes(subtopic) ? true : missing;
      }),
    );
};
