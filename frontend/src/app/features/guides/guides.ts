import { Component, DestroyRef, computed, effect, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideCopy, LucideListChecks, LucideListTree } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintApi } from '../../core/blueprint-api';
import { BlueprintProgress } from '../../core/blueprint-progress';
import { PageOutline } from '../../core/page-outline';
import { TopicApi } from '../../core/topic-api';
import { AreaHint, AreaIntro } from '../../shared/area-intro/area-intro';
import { ProgressBar } from '../../shared/progress-bar/progress-bar';
import { TopicHeader } from '../../shared/topic-header/topic-header';

const HINTS: AreaHint[] = [
  { icon: LucideListTree, title: 'guides.hints.choose.title', text: 'guides.hints.choose.text' },
  { icon: LucideCopy, title: 'guides.hints.copy.title', text: 'guides.hints.copy.text' },
  {
    icon: LucideListChecks,
    title: 'guides.hints.progress.title',
    text: 'guides.hints.progress.text',
  },
];

@Component({
  imports: [AreaIntro, ProgressBar, RouterLink, TopicHeader, TranslatePipe],
  selector: 'app-guides',
  styleUrl: './guides.scss',
  templateUrl: './guides.html',
})
export class Guides {
  private readonly blueprintApi = inject(BlueprintApi);
  protected readonly progress = inject(BlueprintProgress);
  private readonly topicApi = inject(TopicApi);

  readonly topic = input<string>();

  protected readonly hints = HINTS;
  protected readonly summary = toSignal(this.blueprintApi.getSummary(), {
    initialValue: { blueprints: 0, steps: 0 },
  });

  private readonly blueprints = toSignal(this.blueprintApi.getAll(), { initialValue: [] });

  private readonly topicResource = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.topicApi.getBySlug(params),
  });

  protected readonly currentTopic = this.topicResource.value;

  protected readonly topicBlueprints = computed(() =>
    this.blueprints().filter((blueprint) => blueprint.topic === this.topic()),
  );

  constructor() {
    const outline = inject(PageOutline);
    effect(() =>
      outline.set(
        this.currentTopic()
          ? this.topicBlueprints().map((blueprint) => ({
              id: blueprint.slug,
              label: blueprint.title,
            }))
          : [],
      ),
    );
    inject(DestroyRef).onDestroy(() => outline.clear());
  }
}
