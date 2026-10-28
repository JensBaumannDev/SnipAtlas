import { Component, computed, inject, input, model } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { DebugGuide } from '../../../core/debug-guide';
import { resolveOsCode } from '../../../core/os-code';
import { Preferences } from '../../../core/preferences';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { Disclosure } from '../../../shared/disclosure/disclosure';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TermText } from '../../../shared/term-text/term-text';

@Component({
  imports: [CodeBlock, Disclosure, ReportLink, TermText, TranslatePipe],
  selector: 'app-debug-guide-card',
  styleUrl: './debug-guide-card.scss',
  templateUrl: './debug-guide-card.html',
})
export class DebugGuideCard {
  private readonly os = inject(Preferences).os;

  readonly guide = input.required<DebugGuide>();
  readonly expanded = model(false);

  protected readonly steps = computed(() =>
    this.guide().steps.map((step) => ({
      ...step,
      resolved: step.code && {
        language: step.code.language,
        ...resolveOsCode(step.code.code, this.os()),
      },
    })),
  );
}
