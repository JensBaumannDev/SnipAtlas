import { Component, computed, input, model } from '@angular/core';
import { LucideChevronDown } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { Concept } from '../../../core/concept';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { ReportLink } from '../../../shared/report-link/report-link';

@Component({
  imports: [CodeBlock, ReportLink, TranslatePipe, LucideChevronDown],
  selector: 'app-concept-card',
  styleUrl: './concept-card.scss',
  templateUrl: './concept-card.html',
})
export class ConceptCard {
  readonly concept = input.required<Concept>();
  readonly level = input<2 | 3>(3);
  readonly expanded = model(false);

  protected readonly bodyId = computed(() => `${this.concept().slug}-body`);

  protected toggle(): void {
    this.expanded.update((expanded) => !expanded);
  }
}
