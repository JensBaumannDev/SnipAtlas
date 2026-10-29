import { HttpBackend } from '@angular/common/http';
import { mergeApplicationConfig, ApplicationConfig } from '@angular/core';
import { provideServerRendering, withRoutes } from '@angular/ssr';
import { appConfig } from './app.config';
import { serverRoutes } from './app.routes.server';
import { SERVER_ORIGINS, ServerOriginBackend } from './core/http/server-origin-backend';

const serverConfig: ApplicationConfig = {
  providers: [
    provideServerRendering(withRoutes(serverRoutes)),
    {
      provide: SERVER_ORIGINS,
      useValue: { api: process.env['API_URL'], site: process.env['SITE_URL'] },
    },
    { provide: HttpBackend, useClass: ServerOriginBackend },
  ],
};

export const config = mergeApplicationConfig(appConfig, serverConfig);
