import { Component, computed, inject, input, output } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintStep } from '../../../core/blueprint';
import { resolveOsCode } from '../../../core/os-code';
import { Preferences } from '../../../core/preferences';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { ReportLink } from '../../../shared/report-link/report-link';

@Component({
  imports: [CodeBlock, ReportLink, TranslatePipe],
  selector: 'app-guide-step',
  styleUrl: './guide-step.scss',
  templateUrl: './guide-step.html',
})
export class GuideStep {
  private readonly os = inject(Preferences).os;

  readonly step = input.required<BlueprintStep>();
  readonly number = input.required<number>();
  readonly done = input(false);
  readonly toggled = output<void>();

  protected readonly label = computed(() => String(this.number()).padStart(2, '0'));
  protected readonly checkId = computed(() => `${this.step().slug}-done`);
  protected readonly blocks = computed(() =>
    this.step().code.map(({ language, code }) => ({ language, ...resolveOsCode(code, this.os()) })),
  );
}
