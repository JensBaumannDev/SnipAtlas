import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { contentExists, itemExists, itemText, slugExists } from '../../core/content/content-guard';
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
    title: itemText(findWay, (guide) => guide.title, 'pages.debugging'),
    resolve: { description: itemText(findWay, (guide) => guide.summary, 'meta.debugging') },
    canActivate: [slugExists(findWay)],
  },
  { path: ':topic', component: Errors, canActivate: [contentExists] },
  {
    path: ':topic/:slug',
    component: ErrorDetail,
    title: itemText(findError, (error) => error.message, 'pages.debugging'),
    resolve: { description: itemText(findError, (error) => error.meaning, 'meta.debugging') },
    canActivate: [itemExists(findError)],
  },
];
