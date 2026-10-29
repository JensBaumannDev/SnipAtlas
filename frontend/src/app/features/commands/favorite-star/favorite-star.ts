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
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { Entry } from '../../../core/models/entry';
import { Favorites } from '../../../core/user-data/favorites';
import { starIcon } from '../../../core/ui/icons';
import { LoginDialog } from '../../../core/auth/login-dialog';
import { Session } from '../../../core/auth/session';

@Component({
  imports: [TranslatePipe, LucideDynamicIcon],
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

  protected readonly starIcon = starIcon;
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
