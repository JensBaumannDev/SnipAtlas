import { Component, computed, inject, input } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintApi } from '../../core/api/blueprint-api';
import { BlueprintProgress } from '../../core/user-data/blueprint-progress';
import { routeIcon } from '../../core/ui/icons';
import { syncOutline } from '../../core/ui/page-outline';
import { injectTopic } from '../../core/content/topic-resource';
import { AreaInfo } from '../../shared/area-info/area-info';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { ProgressBar } from '../../shared/progress-bar/progress-bar';
import { TopicHeader } from '../../shared/topic-header/topic-header';

@Component({
  imports: [AreaInfo, AreaIntro, ProgressBar, RouterLink, TopicHeader, TranslatePipe],
  selector: 'app-guides',
  styleUrl: './guides.scss',
  templateUrl: './guides.html',
})
export class Guides {
  private readonly blueprintApi = inject(BlueprintApi);
  protected readonly progress = inject(BlueprintProgress);

  readonly topic = input<string>();

  protected readonly icon = routeIcon;
  protected readonly infoSections = ['purpose', 'structure', 'steps'];
  protected readonly summary = toSignal(this.blueprintApi.getSummary(), {
    initialValue: { blueprints: 0, steps: 0 },
  });

  protected readonly blueprints = toSignal(this.blueprintApi.getAll(), { initialValue: [] });

  protected readonly currentTopic = injectTopic(this.topic);

  protected readonly topicBlueprints = computed(() =>
    this.blueprints().filter((blueprint) => blueprint.topic === this.topic()),
  );

  constructor() {
    syncOutline(() =>
      this.currentTopic()
        ? this.topicBlueprints().map((blueprint) => ({
            id: blueprint.slug,
            label: blueprint.title,
          }))
        : [],
    );
  }
}
