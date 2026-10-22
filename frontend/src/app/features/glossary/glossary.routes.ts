import { Routes } from '@angular/router';
import { Glossary } from './glossary';

export const GLOSSARY_ROUTES: Routes = [
  { path: '', component: Glossary },
  { path: ':topic', component: Glossary },
  { path: ':topic/:subtopic', component: Glossary },
];
