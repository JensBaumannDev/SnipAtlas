import { Component, DOCUMENT, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintProgress } from '../../../core/blueprint-progress';
import { Favorites } from '../../../core/favorites';
import { downloadJson } from '../../../core/file-download';
import { Session } from '../../../core/session';
import { UserRequestApi } from '../../../core/user-request-api';
import { AccountDelete } from './account-delete/account-delete';
import { AccountEmail } from './account-email/account-email';
import { AccountPassword } from './account-password/account-password';

const EXPORT_FILE = 'snipatlas-daten.json';

@Component({
  imports: [AccountDelete, AccountEmail, AccountPassword, TranslatePipe],
  selector: 'app-profile-account',
  styleUrl: './profile-account.scss',
  templateUrl: './profile-account.html',
})
export class ProfileAccount {
  private readonly document = inject(DOCUMENT);
  private readonly router = inject(Router);
  private readonly session = inject(Session);
  private readonly progress = inject(BlueprintProgress);
  private readonly favorites = inject(Favorites);
  private readonly requests = toSignal(inject(UserRequestApi).getMine(), { initialValue: [] });

  protected download(): void {
    downloadJson(this.document, EXPORT_FILE, {
      account: this.session.user(),
      favorites: this.favorites.list(),
      progress: this.progress.done(),
      requests: this.requests(),
    });
  }

  protected logout(): void {
    this.session.logout();
    this.router.navigateByUrl('/');
  }
}
