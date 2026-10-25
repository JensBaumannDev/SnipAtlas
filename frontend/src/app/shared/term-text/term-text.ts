import { Component, computed, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { GlossaryTerm } from '../../core/glossary-term';
import { TermLinker } from '../../core/term-linker';

let nextId = 0;

@Component({
  imports: [RouterLink, TranslatePipe],
  selector: 'app-term-text',
  styleUrl: './term-text.scss',
  templateUrl: './term-text.html',
  host: {
    '(keydown.escape)': 'close()',
  },
})
export class TermText {
  private readonly linker = inject(TermLinker);

  readonly text = input.required<string>();

  protected readonly definitionId = `term-text-${nextId++}`;
  protected readonly parts = computed(() => this.linker.split(this.text()));
  protected readonly open = signal<GlossaryTerm | undefined>(undefined);

  protected toggle(term: GlossaryTerm): void {
    this.open.update((current) => (current?.slug === term.slug ? undefined : term));
  }

  protected close(): void {
    this.open.set(undefined);
  }
}
