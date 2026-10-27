import { Component, computed, inject, input, model } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { firstCodeLine } from '../../../core/code-highlight';
import { Entry } from '../../../core/entry';
import { chevronDownIcon } from '../../../core/icons';
import { resolveOsCode } from '../../../core/os-code';
import { Preferences } from '../../../core/preferences';
import { ProjectValues, fillPlaceholders } from '../../../core/project-values';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TermText } from '../../../shared/term-text/term-text';
import { FavoriteStar } from '../favorite-star/favorite-star';

@Component({
  imports: [
    CodeBlock,
    FavoriteStar,
    ReportLink,
    RouterLink,
    TermText,
    TranslatePipe,
    LucideDynamicIcon,
  ],
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

  protected readonly chevronDownIcon = chevronDownIcon;
  protected readonly resolved = computed(() => resolveOsCode(this.entry().code, this.os()));
  protected readonly peek = computed(() =>
    firstCodeLine(
      fillPlaceholders(this.resolved().code, this.project.values(), (key) => `<${key}>`),
    ),
  );
  protected readonly bodyId = computed(() => `${this.entry().slug}-body`);
  protected readonly link = computed(() => {
    const { topic, subtopic, slug } = this.entry();
    return ['/befehle', topic, subtopic, slug];
  });

  protected toggle(): void {
    this.expanded.update((expanded) => !expanded);
  }
}
