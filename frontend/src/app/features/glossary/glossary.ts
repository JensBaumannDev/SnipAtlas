import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { GlossaryApi } from '../../core/glossary-api';
import { GlossaryTerm } from '../../core/glossary-term';
import { bookAIcon, searchIcon } from '../../core/icons';
import { syncOutline } from '../../core/page-outline';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { ReportLink } from '../../shared/report-link/report-link';

interface LetterGroup {
  letter: string;
  terms: GlossaryTerm[];
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
  private readonly terms = toSignal(inject(GlossaryApi).getAll(), { initialValue: [] });

  protected readonly searchIcon = searchIcon;
  protected readonly icon = bookAIcon;
  protected readonly total = computed(() => this.terms().length);

  protected readonly query = new FormControl('', { nonNullable: true });
  private readonly queryValue = toSignal(this.query.valueChanges, { initialValue: '' });

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
    const sorted = [...this.filtered()].sort((a, b) =>
      a.term.localeCompare(b.term, 'de', { sensitivity: 'base' }),
    );
    const groups: LetterGroup[] = [];
    for (const term of sorted) {
      const letter = term.term.charAt(0).toUpperCase();
      const group = groups.at(-1);
      if (group?.letter === letter) {
        group.terms.push(term);
      } else {
        groups.push({ letter, terms: [term] });
      }
    }
    return groups;
  });

  constructor() {
    syncOutline(() =>
      this.groups().map((group) => ({ id: this.letterId(group.letter), label: group.letter })),
    );
  }

  protected letterId(letter: string): string {
    return `letter-${letter.toLowerCase()}`;
  }
}
