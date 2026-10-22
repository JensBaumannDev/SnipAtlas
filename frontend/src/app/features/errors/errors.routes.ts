import { Routes } from '@angular/router';
import { Errors } from './errors';

export const ERRORS_ROUTES: Routes = [
  { path: '', component: Errors },
  { path: ':topic', component: Errors },
];
