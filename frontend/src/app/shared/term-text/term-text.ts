import { Component, computed, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { GlossaryTerm } from '../../core/models/glossary-term';
import { TermLinker, TextPart } from '../../core/content/term-linker';
import { arrowRightIcon } from '../../core/ui/icons';

const PARAGRAPH_BREAK = /\n\s*\n/;

let nextId = 0;

function toParagraphs(parts: readonly TextPart[]): TextPart[][] {
  const paragraphs: TextPart[][] = [[]];
  for (const part of parts) {
    const [first = '', ...rest] = part.term ? [part.text] : part.text.split(PARAGRAPH_BREAK);
    paragraphs[paragraphs.length - 1].push({ ...part, text: first });
    paragraphs.push(...rest.map((text) => [{ text }]));
  }
  return paragraphs;
}

@Component({
  imports: [LucideDynamicIcon, RouterLink, TranslatePipe],
  selector: 'app-term-text',
  styleUrl: './term-text.scss',
  templateUrl: './term-text.html',
  host: {
    '(keydown.escape)': 'close()',
  },
})
export class TermText {
  protected readonly arrowRightIcon = arrowRightIcon;

  private readonly linker = inject(TermLinker);

  readonly text = input.required<string>();

  protected readonly definitionId = `term-text-${nextId++}`;
  protected readonly paragraphs = computed(() => toParagraphs(this.linker.split(this.text())));
  protected readonly open = signal<GlossaryTerm | undefined>(undefined);

  protected toggle(term: GlossaryTerm): void {
    this.open.update((current) => (current?.slug === term.slug ? undefined : term));
  }

  protected close(): void {
    this.open.set(undefined);
  }
}
