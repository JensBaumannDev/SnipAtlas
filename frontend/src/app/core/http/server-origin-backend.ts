import { FetchBackend, HttpBackend, HttpEvent, HttpRequest } from '@angular/common/http';
import { InjectionToken, Service, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface ServerOrigins {
  api?: string;
  site?: string;
}

export const SERVER_ORIGINS = new InjectionToken<ServerOrigins>('SERVER_ORIGINS');

@Service()
export class ServerOriginBackend implements HttpBackend {
  private readonly backend = inject(FetchBackend);
  private readonly origins = inject(SERVER_ORIGINS);

  handle(request: HttpRequest<unknown>): Observable<HttpEvent<unknown>> {
    const url = new URL(request.url);
    const origin = url.pathname.startsWith('/api/') ? this.origins.api : this.origins.site;
    if (!origin) {
      return this.backend.handle(request);
    }
    return this.backend.handle(request.clone({ url: `${origin}${url.pathname}${url.search}` }));
  }
}
