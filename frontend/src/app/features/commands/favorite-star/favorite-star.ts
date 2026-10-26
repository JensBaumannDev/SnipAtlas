import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { LucideStar } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { Entry } from '../../../core/entry';
import { Favorites } from '../../../core/favorites';
import { LoginDialog } from '../../../core/login-dialog';
import { Session } from '../../../core/session';

@Component({
  imports: [TranslatePipe, LucideStar],
  selector: 'app-favorite-star',
  styleUrl: './favorite-star.scss',
  templateUrl: './favorite-star.html',
})
export class FavoriteStar {
  private readonly favorites = inject(Favorites);
  private readonly session = inject(Session);
  private readonly loginDialog = inject(LoginDialog);
  private readonly injector = inject(Injector);

  private readonly star = viewChild.required<ElementRef<HTMLButtonElement>>('star');

  readonly entry = input.required<Entry>();

  protected readonly favorite = computed(() => this.favorites.has(this.entry()));
  protected readonly loginHint = signal(false);

  protected toggle(): void {
    if (!this.session.user()) {
      this.loginHint.set(true);
      return;
    }
    this.favorites.toggle(this.entry());
  }

  protected async login(): Promise<void> {
    const dialogRef = await this.loginDialog.open();
    dialogRef.closed.subscribe(() => {
      if (!this.session.user()) {
        return;
      }
      this.loginHint.set(false);
      afterNextRender(() => this.star().nativeElement.focus(), { injector: this.injector });
    });
  }
}
