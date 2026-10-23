import { Component, computed, inject, input } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { Blueprint } from '../../core/blueprint';
import { BlueprintApi } from '../../core/blueprint-api';
import { BlueprintProgress } from '../../core/blueprint-progress';
import { Topic } from '../../core/topic';
import { TopicApi } from '../../core/topic-api';
import { topicIcon, topicLogo } from '../../core/topic-logos';
import { ProgressBar } from './progress-bar/progress-bar';

interface BlueprintSection {
  topic: Topic;
  blueprints: Blueprint[];
}

@Component({
  imports: [ProgressBar, RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-guides',
  styleUrl: './guides.scss',
  templateUrl: './guides.html',
})
export class Guides {
  private readonly progress = inject(BlueprintProgress);

  readonly topic = input<string>();

  protected readonly topicLogo = topicLogo;
  protected readonly topicIcon = topicIcon;

  private readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  private readonly blueprints = toSignal(inject(BlueprintApi).getAll(), { initialValue: [] });

  protected readonly currentTopic = computed(() =>
    this.groups()
      .flatMap((group) => group.topics)
      .find((topic) => topic.slug === this.topic()),
  );

  protected readonly sections = computed<BlueprintSection[]>(() => {
    const current = this.currentTopic();
    const topics = current ? [current] : this.groups().flatMap((group) => group.topics);
    return topics
      .map((topic) => ({
        topic,
        blueprints: this.blueprints().filter((blueprint) => blueprint.topic === topic.slug),
      }))
      .filter((section) => section.blueprints.length);
  });

  protected doneCount(blueprint: Blueprint): number {
    const done = this.progress.doneSteps(blueprint.slug);
    return blueprint.steps.filter((step) => done.includes(step.slug)).length;
  }
}
