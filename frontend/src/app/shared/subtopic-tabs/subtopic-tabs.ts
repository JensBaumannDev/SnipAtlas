import { Component, input } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Subtopic } from '../../core/models/topic';
import { KEEP_SCROLL } from '../../core/ui/scroll-restoration';

@Component({
  imports: [RouterLink, RouterLinkActive, TranslatePipe],
  selector: 'app-subtopic-tabs',
  styleUrl: './subtopic-tabs.scss',
  templateUrl: './subtopic-tabs.html',
})
export class SubtopicTabs {
  readonly path = input.required<string[]>();
  readonly subtopics = input.required<readonly Subtopic[]>();

  protected readonly keepScroll = KEEP_SCROLL;
}
