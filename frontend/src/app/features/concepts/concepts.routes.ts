import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivateFn, ResolveFn, Routes } from '@angular/router';
import { map } from 'rxjs';
import { Concept } from '../../core/concept';
import { ConceptApi } from '../../core/concept-api';
import { contentExists, notFound } from '../../core/content-guard';
import { ConceptDetail } from './concept-detail/concept-detail';
import { Concepts } from './concepts';

function matches(concept: Concept | undefined, route: ActivatedRouteSnapshot): concept is Concept {
  return (
    concept?.topic === route.paramMap.get('topic') &&
    concept.subtopic === route.paramMap.get('subtopic')
  );
}

const conceptExists: CanActivateFn = (route) => {
  const missing = notFound();
  return inject(ConceptApi)
    .getBySlug(route.paramMap.get('slug') ?? '')
    .pipe(map((concept) => (matches(concept, route) ? true : missing)));
};

const conceptTitle: ResolveFn<string> = (route) =>
  inject(ConceptApi)
    .getBySlug(route.paramMap.get('slug') ?? '')
    .pipe(map((concept) => concept?.title ?? 'pages.concepts'));

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
    title: conceptTitle,
    canActivate: [conceptExists],
  },
];
