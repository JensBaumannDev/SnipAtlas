import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { ReportLink } from '../report-link/report-link';

@Component({
  imports: [ReportLink, RouterLink, TranslatePipe],
  selector: 'app-item-links',
  styleUrl: './item-links.scss',
  templateUrl: './item-links.html',
})
export class ItemLinks {
  readonly link = input.required<readonly string[]>();
  readonly title = input.required<string>();
  readonly report = input.required<string>();
}
