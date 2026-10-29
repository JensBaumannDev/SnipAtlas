import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideHttpClient, withInterceptors, withXsrfConfiguration } from '@angular/common/http';
import {
  TitleStrategy,
  provideRouter,
  withComponentInputBinding,
  withInMemoryScrolling,
  withRouterConfig,
} from '@angular/router';
import { TranslateService, provideTranslateService } from '@ngx-translate/core';
import { provideTranslateHttpLoader } from '@ngx-translate/http-loader';
import { routes } from './app.routes';
import { apiErrorInterceptor } from './core/http/api-error-interceptor';
import { languageInterceptor } from './core/http/language-interceptor';
import { PageTitle } from './core/ui/page-title';
import { Preferences } from './core/user-data/preferences';
import { Session } from './core/auth/session';
import { SettingsSync } from './core/user-data/settings-sync';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(
      routes,
      withComponentInputBinding(),
      withInMemoryScrolling({ anchorScrolling: 'enabled', scrollPositionRestoration: 'enabled' }),
      withRouterConfig({ onSameUrlNavigation: 'reload' }),
    ),
    provideHttpClient(
      withInterceptors([languageInterceptor, apiErrorInterceptor]),
      withXsrfConfiguration({ cookieName: 'csrftoken', headerName: 'X-CSRFToken' }),
    ),
    provideTranslateService({
      fallbackLang: 'de',
      loader: provideTranslateHttpLoader({
        prefix: './i18n/',
        suffix: '.json',
      }),
    }),
    provideAppInitializer(() => inject(TranslateService).use(inject(Preferences).language())),
    provideAppInitializer(() => {
      inject(SettingsSync);
    }),
    provideAppInitializer(() => inject(Session).restore()),
    { provide: TitleStrategy, useExisting: PageTitle },
  ],
};
