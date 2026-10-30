import { Component, inject } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { Notifications } from '../../core/ui/notifications';

@Component({
  imports: [TranslatePipe],
  selector: 'app-vscode-theme',
  styleUrl: './vscode-theme.scss',
  templateUrl: './vscode-theme.html',
})
export class VscodeTheme {
  private readonly notifications = inject(Notifications);

  protected downloaded(): void {
    this.notifications.show('notifications.downloaded');
  }
}
