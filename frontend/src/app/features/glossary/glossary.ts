import { Component, computed, effect, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { GlossaryApi } from '../../core/api/glossary-api';
import { GlossaryTerm } from '../../core/models/glossary-term';
import { bookAIcon, searchIcon, xIcon } from '../../core/ui/icons';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { ReportLink } from '../../shared/report-link/report-link';

interface LetterGroup {
  letter: string;
  terms: GlossaryTerm[];
}

interface LetterLink {
  letter: string;
  active: boolean;
}

const ALPHABET = [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'];
const OTHER = '#';

function letterOf(term: string): string {
  const first = term.normalize('NFD').match(/[a-z0-9]/i)?.[0] ?? OTHER;
  const letter = first.toUpperCase();
  return ALPHABET.includes(letter) ? letter : OTHER;
}

function letterRank(letter: string): number {
  return letter === OTHER ? ALPHABET.length : ALPHABET.indexOf(letter);
}

function sortByLetter(terms: GlossaryTerm[]): GlossaryTerm[] {
  return terms
    .map((term) => ({ term, letter: letterOf(term.term) }))
    .sort(
      (a, b) =>
        letterRank(a.letter) - letterRank(b.letter) ||
        a.term.term.localeCompare(b.term.term, 'de', { sensitivity: 'base' }),
    )
    .map(({ term }) => term);
}

@Component({
  imports: [
    AreaIntro,
    ReactiveFormsModule,
    ReportLink,
    RouterLink,
    TranslatePipe,
    LucideDynamicIcon,
  ],
  selector: 'app-glossary',
  styleUrl: './glossary.scss',
  templateUrl: './glossary.html',
})
export class Glossary {
  private readonly route = inject(ActivatedRoute);
  private readonly routeQuery = toSignal(this.route.queryParamMap, {
    initialValue: this.route.snapshot.queryParamMap,
  });
  private readonly terms = toSignal(inject(GlossaryApi).getAll(), { initialValue: [] });

  protected readonly searchIcon = searchIcon;
  protected readonly xIcon = xIcon;
  protected readonly icon = bookAIcon;
  protected readonly total = computed(() => this.terms().length);

  protected readonly query = new FormControl(this.route.snapshot.queryParamMap.get('q') ?? '', {
    nonNullable: true,
  });
  private readonly queryValue = toSignal(this.query.valueChanges, {
    initialValue: this.query.value,
  });
  protected readonly hasQuery = computed(() => this.queryValue().length > 0);

  protected readonly filtered = computed(() => {
    const words = this.queryValue().trim().toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) {
      return this.terms();
    }
    return this.terms().filter((term) => {
      const haystack = [term.term, ...term.aliases, term.definition].join(' ').toLowerCase();
      return words.every((word) => haystack.includes(word));
    });
  });

  protected readonly groups = computed<LetterGroup[]>(() => {
    const groups: LetterGroup[] = [];
    for (const term of sortByLetter(this.filtered())) {
      const letter = letterOf(term.term);
      const group = groups.at(-1);
      if (group?.letter === letter) {
        group.terms.push(term);
      } else {
        groups.push({ letter, terms: [term] });
      }
    }
    return groups;
  });

  protected readonly letters = computed<LetterLink[]>(() => {
    const present = new Set(this.groups().map((group) => group.letter));
    const extra = [...present].filter((letter) => !ALPHABET.includes(letter));
    return [...ALPHABET, ...extra].map((letter) => ({ letter, active: present.has(letter) }));
  });

  constructor() {
    effect(() => {
      const value = this.routeQuery().get('q') ?? '';
      if (this.query.value !== value) {
        this.query.setValue(value);
      }
    });
  }

  protected letterId(letter: string): string {
    return letter === OTHER ? 'letter-other' : `letter-${letter.toLowerCase()}`;
  }

  protected clearSearch(): void {
    this.query.setValue('');
  }
}
