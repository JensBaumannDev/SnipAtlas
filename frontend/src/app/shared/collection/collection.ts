import { Component, computed, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideStar } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { Favorites } from '../../core/favorites';
import { Session } from '../../core/session';
import { LoginDialog } from '../../features/auth/login-dialog';

@Component({
  imports: [RouterLink, TranslatePipe, LucideStar],
  selector: 'app-collection',
  styleUrl: './collection.scss',
  templateUrl: './collection.html',
})
export class Collection {
  private readonly loginDialog = inject(LoginDialog);

  readonly hint = input('sidebar.collectionHint');
  readonly limit = input<number>();

  protected readonly session = inject(Session);
  protected readonly favorites = inject(Favorites).list;
  protected readonly shown = computed(() => {
    const limit = this.limit();
    return limit ? this.favorites().slice(0, limit) : this.favorites();
  });
  protected readonly hidden = computed(() => this.favorites().length - this.shown().length);

  protected login(): void {
    this.loginDialog.open();
  }
}
