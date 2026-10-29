import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { ConceptApi } from '../../core/api/concept-api';
import { contentExists, itemExists, itemTitle } from '../../core/content/content-guard';
import { ConceptDetail } from './concept-detail/concept-detail';
import { Concepts } from './concepts';

const findConcept = (slug: string) => inject(ConceptApi).getBySlug(slug);

export const CONCEPTS_ROUTES: Routes = [
  { path: '', component: Concepts },
  { path: ':topic', component: Concepts, canActivate: [contentExists] },
  {
    path: ':topic/:subtopic',
    component: Concepts,
    canActivate: [contentExists],
  },
  {
    path: ':topic/:subtopic/:slug',
    component: ConceptDetail,
    title: itemTitle(findConcept, (concept) => concept.title, 'pages.concepts'),
    canActivate: [itemExists(findConcept)],
  },
];
