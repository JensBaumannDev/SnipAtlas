import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { BlueprintApi } from '../../core/blueprint-api';
import { contentExists, itemExists } from '../../core/content-guard';
import { GuideDetail } from './guide-detail/guide-detail';
import { Guides } from './guides';

const findBlueprint = (slug: string) => inject(BlueprintApi).getBySlug(slug);

export const GUIDES_ROUTES: Routes = [
  { path: '', component: Guides },
  { path: ':topic', component: Guides, canActivate: [contentExists] },
  { path: ':topic/:slug', component: GuideDetail, canActivate: [itemExists(findBlueprint)] },
];
