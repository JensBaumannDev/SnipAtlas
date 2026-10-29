import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

export const languageInterceptor: HttpInterceptorFn = (request, next) => {
  if (!request.url.startsWith('/api/')) {
    return next(request);
  }
  const language = inject(TranslateService).getCurrentLang() ?? 'de';
  return next(request.clone({ setHeaders: { 'Accept-Language': language } }));
};
