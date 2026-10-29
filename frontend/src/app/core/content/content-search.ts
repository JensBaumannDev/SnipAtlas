import { Service, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { combineLatest, map } from 'rxjs';
import { Blueprint } from '../models/blueprint';
import { BlueprintApi } from '../api/blueprint-api';
import { Concept, conceptLink } from '../models/concept';
import { ConceptApi } from '../api/concept-api';
import { DebugGuide, debugWayLink } from '../models/debug-guide';
import { DebugGuideApi } from '../api/debug-guide-api';
import { Entry, entryLink } from '../models/entry';
import { EntryApi } from '../api/entry-api';
import { ErrorApi } from '../api/error-api';
import { ErrorMessage, errorLink } from '../models/error-message';
import { SearchResult } from '../models/search-result';

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
      link: entryLink(entry),
    },
    codeText(entry.code),
  );
}

function fromConcept(concept: Concept): SearchItem {
  return toItem({
    area: 'concepts',
    title: concept.title,
    text: concept.summary,
    link: conceptLink(concept),
  });
}

function fromError(error: ErrorMessage): SearchItem {
  return toItem({
    area: 'debugging',
    title: error.message,
    text: error.meaning,
    link: errorLink(error),
  });
}

function fromGuide(guide: DebugGuide): SearchItem {
  const target = guide.topic
    ? { link: ['/fehler', guide.topic], fragment: guide.slug }
    : { link: debugWayLink(guide.slug) };
  return toItem({ area: 'debugging', title: guide.title, text: guide.summary, ...target });
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
