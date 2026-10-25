import { Service, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { GlossaryApi } from './glossary-api';
import { GlossaryTerm } from './glossary-term';

export interface TextPart {
  text: string;
  term?: GlossaryTerm;
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
    const used = new Set<string>();
    let last = 0;
    for (const match of text.matchAll(pattern)) {
      const term = byName.get(match[0].toLowerCase());
      if (!term || used.has(term.slug)) {
        continue;
      }
      used.add(term.slug);
      if (match.index > last) {
        parts.push({ text: text.slice(last, match.index) });
      }
      parts.push({ text: match[0], term });
      last = match.index + match[0].length;
    }
    if (last < text.length) {
      parts.push({ text: text.slice(last) });
    }
    return parts;
  }
}
