import { Component, computed, inject, input, model } from '@angular/core';
import { LucideChevronDown } from '@lucide/angular';
import { firstCodeLine } from '../../../core/code-highlight';
import { Entry } from '../../../core/entry';
import { Preferences } from '../../../core/preferences';
import { CodeBlock } from '../code-block/code-block';

@Component({
  imports: [CodeBlock, LucideChevronDown],
  selector: 'app-entry-card',
  styleUrl: './entry-card.scss',
  templateUrl: './entry-card.html',
})
export class EntryCard {
  private readonly os = inject(Preferences).os;

  readonly entry = input.required<Entry>();
  readonly level = input<2 | 3>(3);
  readonly expanded = model(false);

  private readonly hasOsVariants = computed(() => typeof this.entry().code !== 'string');

  protected readonly code = computed(() => {
    const code = this.entry().code;
    return typeof code === 'string' ? code : code[this.os()];
  });
  protected readonly codeOs = computed(() => (this.hasOsVariants() ? this.os() : undefined));
  protected readonly peek = computed(() => firstCodeLine(this.code()));
  protected readonly bodyId = computed(() => `${this.entry().slug}-body`);

  protected toggle(): void {
    this.expanded.update((expanded) => !expanded);
  }
}
