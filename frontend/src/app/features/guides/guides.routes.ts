import { Routes } from '@angular/router';
import { GuideDetail } from './guide-detail/guide-detail';
import { Guides } from './guides';

export const GUIDES_ROUTES: Routes = [
  { path: '', component: Guides },
  { path: ':topic', component: Guides },
  { path: ':topic/:slug', component: GuideDetail },
];
