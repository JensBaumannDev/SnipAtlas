import { Component, input, model } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { DebugGuide } from '../../../core/models/debug-guide';
import { Disclosure } from '../../../shared/disclosure/disclosure';
import { ReportLink } from '../../../shared/report-link/report-link';
import { DebugGuideSteps } from '../debug-guide-steps/debug-guide-steps';

@Component({
  imports: [DebugGuideSteps, Disclosure, ReportLink, TranslatePipe],
  selector: 'app-debug-guide-card',
  styleUrl: './debug-guide-card.scss',
  templateUrl: './debug-guide-card.html',
})
export class DebugGuideCard {
  readonly guide = input.required<DebugGuide>();
  readonly expanded = model(false);
}
