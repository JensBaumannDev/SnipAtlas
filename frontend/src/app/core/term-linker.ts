import { Service, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { GlossaryApi } from './glossary-api';
import { GlossaryTerm } from './glossary-term';
import { pushText } from './text-parts';

export interface TextPart {
  text: string;
  term?: GlossaryTerm;
}

interface TermMention {
  index: number;
  name: string;
  term: GlossaryTerm;
}

function firstMentions(
  text: string,
  pattern: RegExp,
  byName: ReadonlyMap<string, GlossaryTerm>,
): TermMention[] {
  const used = new Set<GlossaryTerm>();
  return [...text.matchAll(pattern)].flatMap((match) => {
    const term = byName.get(match[0].toLowerCase());
    if (!term || used.has(term)) {
      return [];
    }
    used.add(term);
    return [{ index: match.index, name: match[0], term }];
  });
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

@Service()
export class TermLinker {
  private readonly terms = toSignal(inject(GlossaryApi).getAll(), { initialValue: [] });

  private readonly matcher = computed(() => {
    const byName = new Map<string, GlossaryTerm>();
    for (const term of this.terms()) {
      for (const name of [term.term, ...term.aliases]) {
        byName.set(name.toLowerCase(), term);
      }
    }
    const names = [...byName.keys()].sort((a, b) => b.length - a.length).map(escapeRegExp);
    const pattern = names.length
      ? new RegExp(`(?<![\\p{L}\\p{N}_])(?:${names.join('|')})(?![\\p{L}\\p{N}_])`, 'giu')
      : undefined;
    return { byName, pattern };
  });

  split(text: string): TextPart[] {
    const { byName, pattern } = this.matcher();
    if (!pattern) {
      return [{ text }];
    }
    const parts: TextPart[] = [];
    let last = 0;
    for (const { index, name, term } of firstMentions(text, pattern, byName)) {
      pushText(parts, text.slice(last, index));
      parts.push({ text: name, term });
      last = index + name.length;
    }
    pushText(parts, text.slice(last));
    return parts;
  }
}
