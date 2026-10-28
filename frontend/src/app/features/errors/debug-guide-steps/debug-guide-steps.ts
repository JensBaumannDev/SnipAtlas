import { Component, computed, inject, input } from '@angular/core';
import { DebugGuide } from '../../../core/debug-guide';
import { resolveOsCode } from '../../../core/os-code';
import { Preferences } from '../../../core/preferences';
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
