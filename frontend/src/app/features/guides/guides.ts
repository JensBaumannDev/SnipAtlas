import { Component, DestroyRef, computed, effect, inject, input } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideCopy, LucideDynamicIcon, LucideListChecks, LucideListTree } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintApi } from '../../core/blueprint-api';
import { BlueprintProgress } from '../../core/blueprint-progress';
import { PageOutline } from '../../core/page-outline';
import { TopicApi } from '../../core/topic-api';
import { topicIcon, topicLogo } from '../../core/topic-logos';
import { AreaHint, AreaIntro } from '../../shared/area-intro/area-intro';
import { ProgressBar } from '../../shared/progress-bar/progress-bar';

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
  imports: [AreaIntro, ProgressBar, RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-guides',
  styleUrl: './guides.scss',
  templateUrl: './guides.html',
})
export class Guides {
  private readonly blueprintApi = inject(BlueprintApi);
  protected readonly progress = inject(BlueprintProgress);

  readonly topic = input<string>();

  protected readonly topicLogo = topicLogo;
  protected readonly topicIcon = topicIcon;
  protected readonly hints = HINTS;
  protected readonly summary = toSignal(this.blueprintApi.getSummary(), {
    initialValue: { blueprints: 0, steps: 0 },
  });

  private readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  private readonly blueprints = toSignal(this.blueprintApi.getAll(), { initialValue: [] });

  protected readonly currentTopic = computed(() =>
    this.groups()
      .flatMap((group) => group.topics)
      .find((topic) => topic.slug === this.topic()),
  );

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
