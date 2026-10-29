import { HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { Observable, OperatorFunction, catchError, of, shareReplay, throwError } from 'rxjs';

export function cachedPerLanguage<T>(load: () => Observable<T>): () => Observable<T> {
  const translate = inject(TranslateService);
  const cache = new Map<string, Observable<T>>();
  return () => {
    const language = translate.getCurrentLang() ?? 'de';
    const cached = cache.get(language) ?? load().pipe(shareReplay(1));
    cache.set(language, cached);
    return cached;
  };
}

export function notFoundAsUndefined<T>(): OperatorFunction<T, T | undefined> {
  return catchError((error: unknown) =>
    error instanceof HttpErrorResponse && error.status === 404
      ? of(undefined)
      : throwError(() => error),
  );
}
