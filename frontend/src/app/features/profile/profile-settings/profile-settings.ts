import { Component, inject } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { Session } from '../../../core/session';
import { Settings } from '../../settings/settings';

@Component({
  imports: [Settings, TranslatePipe],
  selector: 'app-profile-settings',
  styleUrl: './profile-settings.scss',
  templateUrl: './profile-settings.html',
})
export class ProfileSettings {
  protected readonly session = inject(Session);

  protected setNotify(event: Event): void {
    if (event.target instanceof HTMLInputElement) {
      this.session.update({ notifyByMail: event.target.checked });
    }
  }
}
