import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

export interface RelatedItem {
  slug: string;
  title: string;
  link: readonly string[];
}

@Component({
  imports: [RouterLink, TranslatePipe],
  selector: 'app-related-list',
  styleUrl: './related-list.scss',
  templateUrl: './related-list.html',
})
export class RelatedList {
  readonly name = input.required<string>();
  readonly items = input.required<readonly RelatedItem[]>();
}
