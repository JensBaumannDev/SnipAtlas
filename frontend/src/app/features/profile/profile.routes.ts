import { inject } from '@angular/core';
import { CanActivateFn, Router, Routes } from '@angular/router';
import { Session } from '../../core/session';
import { Profile } from './profile';
import { ProfileAccount } from './profile-account/profile-account';
import { ProfileOverview } from './profile-overview/profile-overview';
import { ProfileRequests } from './profile-requests/profile-requests';
import { ProfileSettings } from './profile-settings/profile-settings';

const signedIn: CanActivateFn = () =>
  inject(Session).user() ? true : inject(Router).createUrlTree(['/']);

export const PROFILE_ROUTES: Routes = [
  {
    path: '',
    component: Profile,
    canActivate: [signedIn],
    children: [
      { path: '', component: ProfileOverview },
      { path: 'anfragen', component: ProfileRequests },
      { path: 'einstellungen', component: ProfileSettings },
      { path: 'konto', component: ProfileAccount },
    ],
  },
];
