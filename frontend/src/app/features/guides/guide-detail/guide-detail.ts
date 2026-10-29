import { Component, computed, inject, input } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintApi } from '../../../core/api/blueprint-api';
import { BlueprintProgress } from '../../../core/user-data/blueprint-progress';
import { syncOutline } from '../../../core/ui/page-outline';
import { placeholderKeys } from '../../../core/user-data/project-values';
import { injectTopic } from '../../../core/content/topic-resource';
import { ProgressBar } from '../../../shared/progress-bar/progress-bar';
import { ProjectForm } from '../../../shared/project-form/project-form';
import { GuideStep } from '../guide-step/guide-step';

@Component({
  imports: [GuideStep, ProgressBar, ProjectForm, RouterLink, TranslatePipe],
  selector: 'app-guide-detail',
  styleUrl: './guide-detail.scss',
  templateUrl: './guide-detail.html',
})
export class GuideDetail {
  private readonly blueprintApi = inject(BlueprintApi);
  private readonly progress = inject(BlueprintProgress);

  readonly topic = input.required<string>();
  readonly slug = input.required<string>();

  private readonly resource = rxResource({
    params: () => this.slug(),
    stream: ({ params }) => this.blueprintApi.getBySlug(params),
  });

  protected readonly blueprint = this.resource.value;
  protected readonly currentTopic = injectTopic(this.topic);

  private readonly doneSteps = computed(() => this.progress.doneSteps(this.slug()));

  protected readonly projectKeys = computed(() => {
    const codes =
      this.blueprint()?.steps.flatMap((step) =>
        step.code.flatMap(({ code }) => (typeof code === 'string' ? [code] : Object.values(code))),
      ) ?? [];
    return placeholderKeys(codes.join('\n'));
  });

  protected readonly doneCount = computed(() => {
    const blueprint = this.blueprint();
    return blueprint ? this.progress.doneCount(blueprint) : 0;
  });

  constructor() {
    syncOutline(
      () => this.blueprint()?.steps.map((step) => ({ id: step.slug, label: step.title })) ?? [],
    );
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
