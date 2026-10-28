import { Component, inject, input } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { TranslatePipe } from '@ngx-translate/core';
import { DebugGuideApi } from '../../../core/debug-guide-api';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TopicHeader } from '../../../shared/topic-header/topic-header';
import { DebugGuideSteps } from '../debug-guide-steps/debug-guide-steps';

@Component({
  imports: [DebugGuideSteps, ReportLink, TopicHeader, TranslatePipe],
  selector: 'app-debug-way',
  styleUrl: './debug-way.scss',
  templateUrl: './debug-way.html',
})
export class DebugWay {
  private readonly debugGuideApi = inject(DebugGuideApi);

  readonly slug = input.required<string>();

  private readonly guideResource = rxResource({
    params: () => this.slug(),
    stream: ({ params }) => this.debugGuideApi.getWay(params),
  });

  protected readonly guide = this.guideResource.value;
}
