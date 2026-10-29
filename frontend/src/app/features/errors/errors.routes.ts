import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { contentExists, itemExists, itemTitle, slugExists } from '../../core/content/content-guard';
import { DEBUG_PATH } from '../../core/models/debug-guide';
import { DebugGuideApi } from '../../core/api/debug-guide-api';
import { ErrorApi } from '../../core/api/error-api';
import { DebugWay } from './debug-way/debug-way';
import { ErrorDetail } from './error-detail/error-detail';
import { Errors } from './errors';

const findError = (slug: string) => inject(ErrorApi).getBySlug(slug);
const findWay = (slug: string) => inject(DebugGuideApi).getWay(slug);

export const ERRORS_ROUTES: Routes = [
  { path: '', component: Errors },
  {
    path: `${DEBUG_PATH}/:slug`,
    component: DebugWay,
    title: itemTitle(findWay, (guide) => guide.title, 'pages.debugging'),
    canActivate: [slugExists(findWay)],
  },
  { path: ':topic', component: Errors, canActivate: [contentExists] },
  {
    path: ':topic/:slug',
    component: ErrorDetail,
    title: itemTitle(findError, (error) => error.message, 'pages.debugging'),
    canActivate: [itemExists(findError)],
  },
];
