import { inject } from '@angular/core';
import { CanActivateFn, Routes } from '@angular/router';
import { map } from 'rxjs';
import { BlueprintApi } from '../../core/blueprint-api';
import { contentExists, notFound } from '../../core/content-guard';
import { GuideDetail } from './guide-detail/guide-detail';
import { Guides } from './guides';

const blueprintExists: CanActivateFn = (route) => {
  const missing = notFound();
  return inject(BlueprintApi)
    .getBySlug(route.paramMap.get('slug') ?? '')
    .pipe(
      map((blueprint) => (blueprint?.topic === route.paramMap.get('topic') ? true : missing)),
    );
};

export const GUIDES_ROUTES: Routes = [
  { path: '', component: Guides },
  { path: ':topic', component: Guides, canActivate: [contentExists] },
  { path: ':topic/:slug', component: GuideDetail, canActivate: [blueprintExists] },
];
