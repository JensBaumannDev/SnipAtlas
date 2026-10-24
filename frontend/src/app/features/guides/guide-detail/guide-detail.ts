import { Component, DestroyRef, computed, effect, inject, input } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintApi } from '../../../core/blueprint-api';
import { BlueprintProgress } from '../../../core/blueprint-progress';
import { PageOutline } from '../../../core/page-outline';
import { TopicApi } from '../../../core/topic-api';
import { ProgressBar } from '../../../shared/progress-bar/progress-bar';
import { GuideStep } from '../guide-step/guide-step';

@Component({
  imports: [GuideStep, ProgressBar, RouterLink, TranslatePipe],
  selector: 'app-guide-detail',
  styleUrl: './guide-detail.scss',
  templateUrl: './guide-detail.html',
})
export class GuideDetail {
  private readonly blueprintApi = inject(BlueprintApi);
  private readonly progress = inject(BlueprintProgress);
  private readonly outline = inject(PageOutline);
  private readonly topicApi = inject(TopicApi);

  readonly topic = input.required<string>();
  readonly slug = input.required<string>();

  private readonly resource = rxResource({
    params: () => this.slug(),
    stream: ({ params }) => this.blueprintApi.getBySlug(params),
  });
  private readonly topicResource = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.topicApi.getBySlug(params),
  });

  protected readonly blueprint = this.resource.value;
  protected readonly currentTopic = this.topicResource.value;

  private readonly doneSteps = computed(() => this.progress.doneSteps(this.slug()));

  protected readonly doneCount = computed(() => {
    const blueprint = this.blueprint();
    return blueprint ? this.progress.doneCount(blueprint) : 0;
  });

  constructor() {
    effect(() =>
      this.outline.set(
        this.blueprint()?.steps.map((step) => ({ id: step.slug, label: step.title })) ?? [],
      ),
    );
    inject(DestroyRef).onDestroy(() => this.outline.clear());
  }

  protected isDone(step: string): boolean {
    return this.doneSteps().includes(step);
  }

  protected toggle(step: string): void {
    this.progress.toggle(this.slug(), step);
  }

  protected reset(): void {
    this.progress.reset(this.slug());
  }
}
