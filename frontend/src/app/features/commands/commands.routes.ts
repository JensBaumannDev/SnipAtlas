import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivateFn, ResolveFn, Routes } from '@angular/router';
import { map } from 'rxjs';
import { Entry } from '../../core/entry';
import { EntryApi } from '../../core/entry-api';
import { contentExists, notFound } from '../../core/content-guard';
import { Commands } from './commands';
import { EntryDetail } from './entry-detail/entry-detail';

function matches(entry: Entry | undefined, route: ActivatedRouteSnapshot): entry is Entry {
  return (
    entry?.topic === route.paramMap.get('topic') &&
    entry.subtopic === route.paramMap.get('subtopic')
  );
}

const entryExists: CanActivateFn = (route) => {
  const missing = notFound();
  return inject(EntryApi)
    .getBySlug(route.paramMap.get('slug') ?? '')
    .pipe(map((entry) => (matches(entry, route) ? true : missing)));
};

const entryTitle: ResolveFn<string> = (route) =>
  inject(EntryApi)
    .getBySlug(route.paramMap.get('slug') ?? '')
    .pipe(map((entry) => entry?.title ?? 'pages.commands'));

export const COMMANDS_ROUTES: Routes = [
  { path: '', component: Commands },
  { path: ':topic', component: Commands, canActivate: [contentExists] },
  {
    path: ':topic/:subtopic',
    component: Commands,
    canActivate: [contentExists],
  },
  {
    path: ':topic/:subtopic/:slug',
    component: EntryDetail,
    title: entryTitle,
    canActivate: [entryExists],
  },
];
