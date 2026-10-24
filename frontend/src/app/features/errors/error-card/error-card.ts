import { Component, computed, input, model } from '@angular/core';
import { LucideChevronDown } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { ErrorMessage } from '../../../core/error-message';
import { ReportLink } from '../../../shared/report-link/report-link';
import { CodeBlock } from '../../commands/code-block/code-block';

@Component({
  imports: [CodeBlock, ReportLink, TranslatePipe, LucideChevronDown],
  selector: 'app-error-card',
  styleUrl: './error-card.scss',
  templateUrl: './error-card.html',
})
export class ErrorCard {
  readonly error = input.required<ErrorMessage>();
  readonly expanded = model(false);

  protected readonly bodyId = computed(() => `${this.error().slug}-body`);

  protected toggle(): void {
    this.expanded.update((expanded) => !expanded);
  }
}
