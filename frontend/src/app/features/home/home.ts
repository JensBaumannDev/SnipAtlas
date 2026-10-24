import { DatePipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import {
  LucideBookText,
  LucideDynamicIcon,
  LucideIcon,
  LucideRoute,
  LucideTerminal,
  LucideTriangleAlert,
} from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { combineLatest, map } from 'rxjs';
import { BlueprintApi } from '../../core/blueprint-api';
import { BlueprintProgress } from '../../core/blueprint-progress';
import { ConceptApi } from '../../core/concept-api';
import { DebugGuideApi } from '../../core/debug-guide-api';
import { EntryApi } from '../../core/entry-api';
import { ErrorApi } from '../../core/error-api';
import { NewsApi } from '../../core/news-api';
import { Preferences } from '../../core/preferences';
import { TopicApi } from '../../core/topic-api';
import { Collection } from '../../shared/collection/collection';
import { SearchBox } from '../../shared/search-box/search-box';
import { TopicLogo } from '../../shared/topic-logo/topic-logo';

interface AreaStat {
  path: string;
  label: string;
  description: string;
  icon: LucideIcon;
  count: number;
}

@Component({
  imports: [
    Collection,
    DatePipe,
    RouterLink,
    SearchBox,
    TopicLogo,
    TranslatePipe,
    LucideDynamicIcon,
  ],
  selector: 'app-home',
  styleUrl: './home.scss',
  templateUrl: './home.html',
})
export class Home {
  private readonly progress = inject(BlueprintProgress);
  private readonly blueprintApi = inject(BlueprintApi);
  private readonly blueprints = toSignal(this.blueprintApi.getAll(), { initialValue: [] });
  private readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  private readonly latest = toSignal(inject(NewsApi).getLatest(), { initialValue: [] });

  protected readonly language = inject(Preferences).language;

  protected readonly stats = toSignal(
    combineLatest([
      inject(EntryApi).getSummary(),
      inject(ConceptApi).getSummary(),
      this.blueprintApi.getSummary(),
      inject(ErrorApi).getSummary(),
      inject(DebugGuideApi).getAll(),
    ]).pipe(
      map(([entries, concepts, blueprints, errors, guides]): AreaStat[] => [
        {
          path: '/befehle',
          label: 'nav.commands',
          description: 'home.areas.commands',
          icon: LucideTerminal,
          count: entries.entries,
        },
        {
          path: '/konzepte',
          label: 'nav.concepts',
          description: 'home.areas.concepts',
          icon: LucideBookText,
          count: concepts.entries,
        },
        {
          path: '/bauplaene',
          label: 'nav.blueprints',
          description: 'home.areas.blueprints',
          icon: LucideRoute,
          count: blueprints.blueprints,
        },
        {
          path: '/debugging',
          label: 'nav.debugging',
          description: 'home.areas.debugging',
          icon: LucideTriangleAlert,
          count: errors.entries + guides.length,
        },
      ]),
    ),
    { initialValue: [] },
  );

  protected readonly news = computed(() => {
    const topics = new Map(
      this.groups()
        .flatMap((group) => group.topics)
        .map((topic) => [topic.slug, topic]),
    );
    return this.latest().map((item) => ({ ...item, topicData: topics.get(item.topic) }));
  });
  protected readonly featured = computed(() => this.news()[0]);

  protected readonly current = computed(() =>
    this.blueprints()
      .map((blueprint) => {
        const doneSteps = this.progress.doneSteps(blueprint.slug);
        const done = this.progress.doneCount(blueprint);
        const total = blueprint.steps.length;
        return {
          blueprint,
          done,
          total,
          percent: Math.round((done / total) * 100),
          next: blueprint.steps.find((step) => !doneSteps.includes(step.slug)),
        };
      })
      .find((item) => item.done > 0 && item.done < item.total),
  );
}
