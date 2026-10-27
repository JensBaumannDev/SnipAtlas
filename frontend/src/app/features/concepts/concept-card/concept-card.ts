import { Component, computed, input, model } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { Concept } from '../../../core/concept';
import { chevronDownIcon } from '../../../core/icons';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TermText } from '../../../shared/term-text/term-text';

@Component({
  imports: [CodeBlock, ReportLink, RouterLink, TermText, TranslatePipe, LucideDynamicIcon],
  selector: 'app-concept-card',
  styleUrl: './concept-card.scss',
  templateUrl: './concept-card.html',
})
export class ConceptCard {
  readonly concept = input.required<Concept>();
  readonly level = input<2 | 3>(3);
  readonly expanded = model(false);

  protected readonly chevronDownIcon = chevronDownIcon;
  protected readonly bodyId = computed(() => `${this.concept().slug}-body`);
  protected readonly link = computed(() => {
    const { topic, subtopic, slug } = this.concept();
    return ['/grundlagen', topic, subtopic, slug];
  });

  protected toggle(): void {
    this.expanded.update((expanded) => !expanded);
  }
}
