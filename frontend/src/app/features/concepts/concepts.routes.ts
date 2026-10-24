import { Routes } from '@angular/router';
import { contentExists } from '../../core/content-guard';
import { Concepts } from './concepts';

export const CONCEPTS_ROUTES: Routes = [
  { path: '', component: Concepts },
  { path: ':topic', component: Concepts, canActivate: [contentExists] },
  {
    path: ':topic/:subtopic',
    component: Concepts,
    canActivate: [contentExists],
  },
];
