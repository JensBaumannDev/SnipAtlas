import { Component, input, model } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { ErrorMessage } from '../../../core/error-message';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { Disclosure } from '../../../shared/disclosure/disclosure';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TermText } from '../../../shared/term-text/term-text';

@Component({
  imports: [CodeBlock, Disclosure, ReportLink, TermText, TranslatePipe],
  selector: 'app-error-card',
  styleUrl: './error-card.scss',
  templateUrl: './error-card.html',
})
export class ErrorCard {
  readonly error = input.required<ErrorMessage>();
  readonly expanded = model(false);
}
