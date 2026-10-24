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
import { BlueprintApi } from '../../core/blueprint-api';
import { BlueprintProgress } from '../../core/blueprint-progress';
import { NewsApi } from '../../core/news-api';
import { Collection } from '../../shared/collection/collection';
import { ProgressBar } from '../guides/progress-bar/progress-bar';

interface Area {
  path: string;
  label: string;
  description: string;
  icon: LucideIcon;
}

const AREAS: Area[] = [
  {
    path: '/befehle',
    label: 'nav.commands',
    description: 'home.areas.commands',
    icon: LucideTerminal,
  },
  {
    path: '/konzepte',
    label: 'nav.concepts',
    description: 'home.areas.concepts',
    icon: LucideBookText,
  },
  {
    path: '/bauplaene',
    label: 'nav.blueprints',
    description: 'home.areas.blueprints',
    icon: LucideRoute,
  },
  {
    path: '/debugging',
    label: 'nav.debugging',
    description: 'home.areas.debugging',
    icon: LucideTriangleAlert,
  },
];

@Component({
  imports: [Collection, DatePipe, ProgressBar, RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-home',
  styleUrl: './home.scss',
  templateUrl: './home.html',
})
export class Home {
  protected readonly areas = AREAS;
  protected readonly news = toSignal(inject(NewsApi).getLatest(), { initialValue: [] });

  private readonly progress = inject(BlueprintProgress);
  private readonly blueprints = toSignal(inject(BlueprintApi).getAll(), { initialValue: [] });

  protected readonly current = computed(() =>
    this.blueprints()
      .map((blueprint) => {
        const done = this.progress.doneSteps(blueprint.slug);
        return {
          blueprint,
          done: blueprint.steps.filter((step) => done.includes(step.slug)).length,
        };
      })
      .find((item) => item.done > 0 && item.done < item.blueprint.steps.length),
  );
}
