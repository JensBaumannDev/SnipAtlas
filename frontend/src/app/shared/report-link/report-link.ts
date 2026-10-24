import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideFlag } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [RouterLink, TranslatePipe, LucideFlag],
  selector: 'app-report-link',
  styleUrl: './report-link.scss',
  templateUrl: './report-link.html',
})
export class ReportLink {
  readonly subject = input.required<string>();
}
