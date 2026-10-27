import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  inject,
  input,
  viewChild,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { Favorites } from '../../core/favorites';
import { starIcon } from '../../core/icons';
import { LoginDialog } from '../../core/login-dialog';
import { Session } from '../../core/session';

@Component({
  imports: [RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-collection',
  styleUrl: './collection.scss',
  templateUrl: './collection.html',
})
export class Collection {
  private readonly loginDialog = inject(LoginDialog);
  private readonly injector = inject(Injector);
  private readonly list = viewChild<ElementRef<HTMLUListElement>>('list');

  readonly hint = input('sidebar.collectionHint');
  readonly limit = input<number>();

  protected readonly session = inject(Session);
  protected readonly favorites = inject(Favorites).list;
  protected readonly starIcon = starIcon;
  protected readonly shown = computed(() => {
    const limit = this.limit();
    return limit ? this.favorites().slice(0, limit) : this.favorites();
  });
  protected readonly hidden = computed(() => this.favorites().length - this.shown().length);

  protected async login(): Promise<void> {
    const dialogRef = await this.loginDialog.open();
    dialogRef.closed.subscribe(() =>
      afterNextRender(() => this.list()?.nativeElement.focus(), { injector: this.injector }),
    );
  }
}
