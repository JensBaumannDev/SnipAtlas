import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideHttpClient, withInterceptors, withXsrfConfiguration } from '@angular/common/http';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import {
  RouteReuseStrategy,
  TitleStrategy,
  provideRouter,
  withComponentInputBinding,
  withInMemoryScrolling,
  withRouterConfig,
  withViewTransitions,
} from '@angular/router';
import { TranslateService, provideTranslateService } from '@ngx-translate/core';
import { provideTranslateHttpLoader } from '@ngx-translate/http-loader';
import { routes } from './app.routes';
import { apiErrorInterceptor } from './core/http/api-error-interceptor';
import { forwardedForInterceptor } from './core/http/forwarded-for-interceptor';
import { languageInterceptor } from './core/http/language-interceptor';
import { ComponentReuseStrategy } from './core/ui/component-reuse-strategy';
import { PageMeta } from './core/ui/page-meta';
import { ScrollRestoration } from './core/ui/scroll-restoration';
import { Preferences } from './core/user-data/preferences';
import { Session } from './core/auth/session';
import { SettingsSync } from './core/user-data/settings-sync';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideClientHydration(withEventReplay()),
    provideRouter(
      routes,
      withComponentInputBinding(),
      withInMemoryScrolling({ anchorScrolling: 'enabled', scrollPositionRestoration: 'disabled' }),
      withRouterConfig({ onSameUrlNavigation: 'reload' }),
      withViewTransitions({ skipInitialTransition: true }),
    ),
    provideHttpClient(
      withInterceptors([languageInterceptor, forwardedForInterceptor, apiErrorInterceptor]),
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
    provideAppInitializer(() => {
      inject(ScrollRestoration);
    }),
    { provide: TitleStrategy, useExisting: PageMeta },
    { provide: RouteReuseStrategy, useExisting: ComponentReuseStrategy },
  ],
};
