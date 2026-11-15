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
import { GlossaryApi } from '../api/glossary-api';
import { GlossaryTerm } from '../models/glossary-term';
import { SearchResult } from '../models/search-result';

const MAX_PER_AREA = 3;

interface SearchItem {
  result: SearchResult;
  title: string;
  content: string;
  aliases: string[];
  description: string;
}

function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase();
}

function toItem(result: SearchResult, options: { aliases?: string[]; extra?: string[] } = {}): SearchItem {
  const aliases = (options.aliases ?? []).map(normalize);
  const description = normalize(result.text);
  return {
    result,
    title: normalize(result.title),
    aliases,
    description,
    content: normalize([result.title, result.text, ...aliases, ...(options.extra ?? [])].join(' ')),
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
    { extra: [codeText(entry.code)] },
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

function fromGlossaryTerm(term: GlossaryTerm): SearchItem {
  return toItem(
    {
      area: 'glossary',
      title: term.term,
      text: term.definition,
      link: ['/begriffe'],
      fragment: term.slug,
    },
    { aliases: term.aliases },
  );
}

function rank(item: SearchItem, terms: string[]): number {
  return terms.reduce((score, term) => {
    const titleScore = item.title === term ? 100 : item.title.startsWith(term) ? 70 : item.title.includes(term) ? 50 : 0;
    const aliasScore = item.aliases.some((alias) => alias === term)
      ? 65
      : item.aliases.some((alias) => alias.startsWith(term))
        ? 45
        : 0;
    const descriptionScore = item.description.includes(term) ? 10 : 0;
    return score + Math.max(titleScore, aliasScore, descriptionScore);
  }, 0);
}

function glossarySummary(query: string, count: number): SearchResult {
  return {
    area: 'glossary',
    title: query,
    text: '',
    link: ['/begriffe'],
    query,
    glossaryMatchCount: count,
  };
}

function limitPerArea(results: readonly SearchResult[]): SearchResult[] {
  const counts = new Map<SearchResult['area'], number>();
  return results.filter((result) => {
    const count = counts.get(result.area) ?? 0;
    counts.set(result.area, count + 1);
    return count < MAX_PER_AREA;
  });
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
      inject(GlossaryApi).getAll(),
    ]).pipe(
      map(([entries, concepts, errors, guides, blueprints, glossaryTerms]) => [
        ...entries.map(fromEntry),
        ...concepts.map(fromConcept),
        ...errors.map(fromError),
        ...guides.map(fromGuide),
        ...blueprints.map(fromBlueprint),
        ...glossaryTerms.map(fromGlossaryTerm),
      ]),
    ),
    { initialValue: [] },
  );

  search(query: string): SearchResult[] {
    const terms = normalize(query).split(/\s+/).filter(Boolean);
    if (!terms.length) {
      return [];
    }
    const matches = this.items().filter((item) => terms.every((term) => item.content.includes(term)));
    const glossaryCount = matches.filter((item) => item.result.area === 'glossary').length;
    const results = matches
      .filter((item) => item.result.area !== 'glossary')
      .sort((a, b) => rank(b, terms) - rank(a, terms))
      .map((item) => item.result);
    const glossary = glossaryCount ? [glossarySummary(query.trim(), glossaryCount)] : [];
    return limitPerArea([...glossary, ...results]);
  }
}
