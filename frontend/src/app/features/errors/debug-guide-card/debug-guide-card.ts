import { Component, computed, inject, input, model } from '@angular/core';
import { LucideChevronDown } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { DebugGuide } from '../../../core/debug-guide';
import { Preferences } from '../../../core/preferences';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { ReportLink } from '../../../shared/report-link/report-link';

@Component({
  imports: [CodeBlock, ReportLink, TranslatePipe, LucideChevronDown],
  selector: 'app-debug-guide-card',
  styleUrl: './debug-guide-card.scss',
  templateUrl: './debug-guide-card.html',
})
export class DebugGuideCard {
  private readonly os = inject(Preferences).os;

  readonly guide = input.required<DebugGuide>();
  readonly expanded = model(false);

  protected readonly bodyId = computed(() => `${this.guide().slug}-body`);
  protected readonly steps = computed(() =>
    this.guide().steps.map((step) => ({
      ...step,
      resolved: step.code && {
        language: step.code.language,
        ...(typeof step.code.code === 'string'
          ? { code: step.code.code, os: undefined }
          : { code: step.code.code[this.os()], os: this.os() }),
      },
    })),
  );

  protected toggle(): void {
    this.expanded.update((expanded) => !expanded);
  }
}
