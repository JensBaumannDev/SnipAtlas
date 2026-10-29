import { Service, inject } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';
import { ActivatedRouteSnapshot, RouterStateSnapshot, TitleStrategy } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription, combineLatest, map, of } from 'rxjs';

const APP_NAME = 'SnipAtlas';
const DEFAULT_DESCRIPTION = 'meta.default';

function ownDescription(route: ActivatedRouteSnapshot): string | undefined {
  const description: unknown = route.data['description'];
  return typeof description === 'string' ? description : undefined;
}

function deepestDescription(snapshot: RouterStateSnapshot): string {
  let route: ActivatedRouteSnapshot | null = snapshot.root;
  let description = DEFAULT_DESCRIPTION;
  while (route) {
    description = ownDescription(route) ?? description;
    route = route.firstChild;
  }
  return description;
}

@Service()
export class PageMeta extends TitleStrategy {
  private readonly title = inject(Title);
  private readonly meta = inject(Meta);
  private readonly translate = inject(TranslateService);
  private subscription?: Subscription;

  override updateTitle(snapshot: RouterStateSnapshot): void {
    this.subscription?.unsubscribe();
    this.subscription = combineLatest([
      this.pageTitle(this.buildTitle(snapshot)),
      this.translate.stream(deepestDescription(snapshot)),
    ]).subscribe(([title, description]: [string, string]) => {
      this.title.setTitle(title);
      this.meta.updateTag({ name: 'description', content: description });
    });
  }

  private pageTitle(key: string | undefined): Observable<string> {
    if (!key) {
      return of(APP_NAME);
    }
    return this.translate.stream(key).pipe(map((text: string) => `${text} · ${APP_NAME}`));
  }
}
