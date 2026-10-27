import { Service, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { combineLatest, map } from 'rxjs';
import { Blueprint } from './blueprint';
import { BlueprintApi } from './blueprint-api';
import { Concept } from './concept';
import { ConceptApi } from './concept-api';
import { DebugGuide } from './debug-guide';
import { DebugGuideApi } from './debug-guide-api';
import { Entry } from './entry';
import { EntryApi } from './entry-api';
import { ErrorApi } from './error-api';
import { ErrorMessage } from './error-message';
import { SearchResult } from './search-result';

const MAX_RESULTS = 8;

interface SearchItem {
  result: SearchResult;
  title: string;
  content: string;
}

function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase();
}

function toItem(result: SearchResult, ...extra: string[]): SearchItem {
  return {
    result,
    title: normalize(result.title),
    content: normalize([result.title, result.text, ...extra].join(' ')),
  };
}

function codeText(code: string | Record<string, string>): string {
  return typeof code === 'string' ? code : Object.values(code).join(' ');
}

function fromEntry(entry: Entry): SearchItem {
  return toItem(
    {
      area: 'commands',
      title: entry.title,
      text: entry.description,
      link: ['/befehle', entry.topic, entry.subtopic, entry.slug],
    },
    codeText(entry.code),
  );
}

function fromConcept(concept: Concept): SearchItem {
  return toItem({
    area: 'concepts',
    title: concept.title,
    text: concept.summary,
    link: ['/grundlagen', concept.topic, concept.subtopic, concept.slug],
  });
}

function fromError(error: ErrorMessage): SearchItem {
  return toItem({
    area: 'debugging',
    title: error.message,
    text: error.meaning,
    link: ['/fehler', error.topic],
    fragment: error.slug,
  });
}

function fromGuide(guide: DebugGuide): SearchItem {
  return toItem({
    area: 'debugging',
    title: guide.title,
    text: guide.summary,
    link: guide.topic ? ['/fehler', guide.topic] : ['/fehler'],
    fragment: guide.slug,
  });
}

function fromBlueprint(blueprint: Blueprint): SearchItem {
  return toItem({
    area: 'blueprints',
    title: blueprint.title,
    text: blueprint.summary,
    link: ['/anleitungen', blueprint.topic, blueprint.slug],
  });
}

function rank(item: SearchItem, terms: string[]): number {
  return terms.reduce(
    (score, term) =>
      score + (item.title.startsWith(term) ? 3 : 0) + (item.title.includes(term) ? 2 : 0),
    0,
  );
}

@Service()
export class ContentSearch {
  private readonly items = toSignal(
    combineLatest([
      inject(EntryApi).getAll(),
      inject(ConceptApi).getAll(),
      inject(ErrorApi).getAll(),
      inject(DebugGuideApi).getAll(),
      inject(BlueprintApi).getAll(),
    ]).pipe(
      map(([entries, concepts, errors, guides, blueprints]) => [
        ...entries.map(fromEntry),
        ...concepts.map(fromConcept),
        ...errors.map(fromError),
        ...guides.map(fromGuide),
        ...blueprints.map(fromBlueprint),
      ]),
    ),
    { initialValue: [] },
  );

  search(query: string): SearchResult[] {
    const terms = normalize(query).split(/\s+/).filter(Boolean);
    if (!terms.length) {
      return [];
    }
    return this.items()
      .filter((item) => terms.every((term) => item.content.includes(term)))
      .sort((a, b) => rank(b, terms) - rank(a, terms))
      .slice(0, MAX_RESULTS)
      .map((item) => item.result);
  }
}
