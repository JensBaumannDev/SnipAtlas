import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Topic } from '../../core/topic';
import { TopicLogo } from '../topic-logo/topic-logo';

@Component({
  imports: [RouterLink, TopicLogo],
  selector: 'app-topic-header',
  styleUrl: './topic-header.scss',
  templateUrl: './topic-header.html',
})
export class TopicHeader {
  readonly topic = input.required<Topic>();
  readonly heading = input.required<string>();
  readonly parentLabel = input<string>();
  readonly parentLink = input<string | string[]>();
}
