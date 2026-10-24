import { Routes } from '@angular/router';
import { contentExists } from '../../core/content-guard';
import { Commands } from './commands';

export const COMMANDS_ROUTES: Routes = [
  { path: '', component: Commands },
  { path: ':topic', component: Commands, canActivate: [contentExists] },
  {
    path: ':topic/:subtopic',
    component: Commands,
    canActivate: [contentExists],
  },
];
