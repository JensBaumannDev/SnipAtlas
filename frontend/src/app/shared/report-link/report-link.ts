import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { flagIcon } from '../../core/ui/icons';

@Component({
  imports: [RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-report-link',
  styleUrl: './report-link.scss',
  templateUrl: './report-link.html',
})
export class ReportLink {
  readonly subject = input.required<string>();

  protected readonly flagIcon = flagIcon;
}
