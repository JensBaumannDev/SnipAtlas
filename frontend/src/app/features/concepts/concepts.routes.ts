import { Routes } from '@angular/router';
import { Concepts } from './concepts';

export const CONCEPTS_ROUTES: Routes = [
  { path: '', component: Concepts },
  { path: ':topic', component: Concepts },
  { path: ':topic/:subtopic', component: Concepts },
];
