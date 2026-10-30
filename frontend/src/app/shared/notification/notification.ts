import { Component, inject } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { circleCheckIcon } from '../../core/ui/icons';
import { Notifications } from '../../core/ui/notifications';

@Component({
  imports: [LucideDynamicIcon, TranslatePipe],
  selector: 'app-notification',
  styleUrl: './notification.scss',
  templateUrl: './notification.html',
})
export class Notification {
  protected readonly notifications = inject(Notifications);
  protected readonly circleCheckIcon = circleCheckIcon;
}
