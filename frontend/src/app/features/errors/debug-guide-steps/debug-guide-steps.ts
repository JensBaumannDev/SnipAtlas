import { Component, computed, inject, input } from '@angular/core';
import { DebugGuide } from '../../../core/models/debug-guide';
import { resolveOsCode } from '../../../core/content/os-code';
import { Preferences } from '../../../core/user-data/preferences';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { TermText } from '../../../shared/term-text/term-text';

@Component({
  imports: [CodeBlock, TermText],
  selector: 'app-debug-guide-steps',
  styleUrl: './debug-guide-steps.scss',
  templateUrl: './debug-guide-steps.html',
})
export class DebugGuideSteps {
  private readonly os = inject(Preferences).os;

  readonly guide = input.required<DebugGuide>();

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
