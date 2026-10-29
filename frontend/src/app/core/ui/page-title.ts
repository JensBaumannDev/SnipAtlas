import { Service, inject } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { Subscription } from 'rxjs';

const APP_NAME = 'SnipAtlas';

@Service()
export class PageTitle extends TitleStrategy {
  private readonly title = inject(Title);
  private readonly translate = inject(TranslateService);
  private subscription?: Subscription;

  override updateTitle(snapshot: RouterStateSnapshot): void {
    const key = this.buildTitle(snapshot);
    this.subscription?.unsubscribe();

    if (!key) {
      this.title.setTitle(APP_NAME);
      return;
    }

    this.subscription = this.translate
      .stream(key)
      .subscribe((text: string) => this.title.setTitle(`${text} · ${APP_NAME}`));
  }
}
