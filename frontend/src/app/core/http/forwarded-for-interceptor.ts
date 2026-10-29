import { HttpInterceptorFn } from '@angular/common/http';
import { REQUEST, inject } from '@angular/core';

export const forwardedForInterceptor: HttpInterceptorFn = (request, next) => {
  const forwardedFor = inject(REQUEST, { optional: true })?.headers.get('x-forwarded-for');
  if (!forwardedFor || !request.url.startsWith('/api/')) {
    return next(request);
  }
  return next(request.clone({ setHeaders: { 'X-Forwarded-For': forwardedFor } }));
};
