import { Component, computed, input } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { Topic } from '../../core/models/topic';
import { topicIcon, topicLogo } from '../../core/ui/topic-logos';

@Component({
  imports: [LucideDynamicIcon],
  selector: 'app-topic-logo',
  styleUrl: './topic-logo.scss',
  templateUrl: './topic-logo.html',
  host: {
    '[style.color]': 'topic().color',
  },
})
export class TopicLogo {
  readonly topic = input.required<Topic>();

  protected readonly logo = computed(() => topicLogo(this.topic().slug));
  protected readonly icon = computed(() => topicIcon(this.topic().slug));
}
