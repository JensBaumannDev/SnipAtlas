import { Component, computed, input, model } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { Concept } from '../../../core/models/concept';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { Disclosure } from '../../../shared/disclosure/disclosure';
import { ItemLinks } from '../../../shared/item-links/item-links';
import { Note } from '../../../shared/note/note';
import { TermText } from '../../../shared/term-text/term-text';

@Component({
  imports: [CodeBlock, Disclosure, ItemLinks, Note, TermText, TranslatePipe],
  selector: 'app-concept-card',
  styleUrl: './concept-card.scss',
  templateUrl: './concept-card.html',
})
export class ConceptCard {
  readonly concept = input.required<Concept>();
  readonly level = input<2 | 3>(3);
  readonly expanded = model(false);

  protected readonly link = computed(() => {
    const { topic, subtopic, slug } = this.concept();
    return ['/grundlagen', topic, subtopic, slug];
  });
}
