import { Component, computed, inject, input, model } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { ErrorMessage } from '../../../core/models/error-message';
import { ContentPaths } from '../../../core/content/content-paths';
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
  private readonly paths = inject(ContentPaths);
  readonly error = input.required<ErrorMessage>();
  readonly expanded = model(false);

  protected readonly link = computed(() => {
    const { topic, slug } = this.error();
    return this.paths.link('debugging', topic, slug);
  });
}
