import { Component, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { ErrorMessage } from '../../../core/error-message';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { TermText } from '../../../shared/term-text/term-text';

@Component({
  imports: [CodeBlock, TermText, TranslatePipe],
  selector: 'app-error-body',
  styleUrl: './error-body.scss',
  templateUrl: './error-body.html',
})
export class ErrorBody {
  readonly error = input.required<ErrorMessage>();
  readonly level = input<2 | 4>(4);
}
