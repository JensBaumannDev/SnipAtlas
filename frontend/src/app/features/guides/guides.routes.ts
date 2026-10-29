import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { BlueprintApi } from '../../core/api/blueprint-api';
import { contentExists, itemExists, itemText } from '../../core/content/content-guard';
import { GuideDetail } from './guide-detail/guide-detail';
import { Guides } from './guides';

const findBlueprint = (slug: string) => inject(BlueprintApi).getBySlug(slug);

export const GUIDES_ROUTES: Routes = [
  { path: '', component: Guides },
  { path: ':topic', component: Guides, canActivate: [contentExists] },
  {
    path: ':topic/:slug',
    component: GuideDetail,
    title: itemText(findBlueprint, (blueprint) => blueprint.title, 'pages.blueprints'),
    resolve: {
      description: itemText(findBlueprint, (blueprint) => blueprint.summary, 'meta.blueprints'),
    },
    canActivate: [itemExists(findBlueprint)],
  },
];
