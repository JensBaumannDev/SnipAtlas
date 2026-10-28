import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { contentExists, itemExists, itemTitle } from '../../core/content-guard';
import { ErrorApi } from '../../core/error-api';
import { ErrorDetail } from './error-detail/error-detail';
import { Errors } from './errors';

const findError = (slug: string) => inject(ErrorApi).getBySlug(slug);

export const ERRORS_ROUTES: Routes = [
  { path: '', component: Errors },
  { path: ':topic', component: Errors, canActivate: [contentExists] },
  {
    path: ':topic/:slug',
    component: ErrorDetail,
    title: itemTitle(findError, (error) => error.message, 'pages.debugging'),
    canActivate: [itemExists(findError)],
  },
];
