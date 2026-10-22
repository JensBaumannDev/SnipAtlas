import { Routes } from '@angular/router';
import { Commands } from './commands';

export const COMMANDS_ROUTES: Routes = [
  { path: '', component: Commands },
  { path: ':topic', component: Commands },
  { path: ':topic/:subtopic', component: Commands },
];
