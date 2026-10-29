import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { contentExists, itemExists, itemTitle } from '../../core/content/content-guard';
import { EntryApi } from '../../core/api/entry-api';
import { Commands } from './commands';
import { EntryDetail } from './entry-detail/entry-detail';

const findEntry = (slug: string) => inject(EntryApi).getBySlug(slug);

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
    title: itemTitle(findEntry, (entry) => entry.title, 'pages.commands'),
    canActivate: [itemExists(findEntry)],
  },
];
