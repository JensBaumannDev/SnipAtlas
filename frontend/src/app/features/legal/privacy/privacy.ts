import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [RouterLink, TranslatePipe],
  selector: 'app-privacy',
  styleUrl: './privacy.scss',
  templateUrl: './privacy.html',
})
export class Privacy {
  protected readonly logItems = ['ip', 'time', 'request', 'status', 'referrer', 'browser'];
  protected readonly storageItems = ['theme', 'os', 'language'];
  protected readonly accountItems = ['login', 'favorites', 'progress', 'settings', 'requests'];
  protected readonly rightItems = [
    'access',
    'rectification',
    'erasure',
    'restriction',
    'portability',
    'objection',
    'withdrawal',
    'complaint',
  ];
}
