import { Component, computed, inject, input, model } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { firstCodeLine } from '../../../core/content/code-highlight';
import { Entry } from '../../../core/models/entry';
import { resolveOsCode } from '../../../core/content/os-code';
import { Preferences } from '../../../core/user-data/preferences';
import { ProjectValues, fillPlaceholders } from '../../../core/user-data/project-values';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { Disclosure } from '../../../shared/disclosure/disclosure';
import { ItemLinks } from '../../../shared/item-links/item-links';
import { TermText } from '../../../shared/term-text/term-text';
import { FavoriteStar } from '../favorite-star/favorite-star';

@Component({
  imports: [CodeBlock, Disclosure, FavoriteStar, ItemLinks, TermText, TranslatePipe],
  selector: 'app-entry-card',
  styleUrl: './entry-card.scss',
  templateUrl: './entry-card.html',
})
export class EntryCard {
  private readonly os = inject(Preferences).os;
  private readonly project = inject(ProjectValues);

  readonly entry = input.required<Entry>();
  readonly level = input<2 | 3>(3);
  readonly expanded = model(false);

  protected readonly resolved = computed(() => resolveOsCode(this.entry().code, this.os()));
  protected readonly peek = computed(() =>
    firstCodeLine(
      fillPlaceholders(this.resolved().code, this.project.values(), (key) => `<${key}>`),
    ),
  );
  protected readonly link = computed(() => {
    const { topic, subtopic, slug } = this.entry();
    return ['/befehle', topic, subtopic, slug];
  });
}
