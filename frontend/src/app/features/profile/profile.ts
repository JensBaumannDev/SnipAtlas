import { DatePipe } from '@angular/common';
import { Component, effect, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Preferences } from '../../core/user-data/preferences';
import { Session } from '../../core/auth/session';

interface ProfileTab {
  path: string;
  label: string;
}

const TABS: ProfileTab[] = [
  { path: '/profil', label: 'profile.tabs.overview' },
  { path: '/profil/anfragen', label: 'profile.tabs.requests' },
  { path: '/profil/einstellungen', label: 'profile.tabs.settings' },
  { path: '/profil/konto', label: 'profile.tabs.account' },
];

@Component({
  imports: [DatePipe, RouterLink, RouterLinkActive, RouterOutlet, TranslatePipe],
  selector: 'app-profile',
  styleUrl: './profile.scss',
  templateUrl: './profile.html',
})
export class Profile {
  protected readonly session = inject(Session);
  protected readonly language = inject(Preferences).language;
  protected readonly tabs = TABS;

  constructor() {
    const router = inject(Router);
    effect(() => {
      if (!this.session.user()) {
        router.navigateByUrl('/');
      }
    });
  }
}
