import { HttpEvent, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, tap, throwError } from 'rxjs';
import { hasCode, isUnreachable } from './api-error';
import { ServerStatus } from './server-status';
import { Session } from './session';

export const apiErrorInterceptor: HttpInterceptorFn = (request, next) => {
  if (!request.url.startsWith('/api/')) {
    return next(request);
  }
  const session = inject(Session);
  const status = inject(ServerStatus);
  const retry = () => session.refreshCsrf().pipe(switchMap(() => next(request)));
  return next(request).pipe(
    catchError((error: unknown) =>
      hasCode(error, 'csrf_failed') ? retry() : throwError(() => error),
    ),
    tap({
      next: (event) => markReachable(event, status),
      error: (error: unknown) => handleError(error, session, status),
    }),
  );
};

function markReachable(event: HttpEvent<unknown>, status: ServerStatus): void {
  if (event instanceof HttpResponse) {
    status.unreachable.set(false);
  }
}

function handleError(error: unknown, session: Session, status: ServerStatus): void {
  status.unreachable.set(isUnreachable(error));
  if (hasCode(error, 'not_authenticated')) {
    session.clear();
  }
}
