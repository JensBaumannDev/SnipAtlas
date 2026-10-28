import { Component, computed, input, model } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { ErrorMessage, errorLink } from '../../../core/error-message';
import { Disclosure } from '../../../shared/disclosure/disclosure';
import { ItemLinks } from '../../../shared/item-links/item-links';
import { ErrorBody } from '../error-body/error-body';

@Component({
  imports: [Disclosure, ErrorBody, ItemLinks, TranslatePipe],
  selector: 'app-error-card',
  styleUrl: './error-card.scss',
  templateUrl: './error-card.html',
})
export class ErrorCard {
  readonly error = input.required<ErrorMessage>();
  readonly expanded = model(false);

  protected readonly link = computed(() => errorLink(this.error()));
}
