import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintApi } from '../../../core/api/blueprint-api';
import { Blueprint } from '../../../core/models/blueprint';
import { BlueprintProgress } from '../../../core/user-data/blueprint-progress';
import { ContentPaths } from '../../../core/content/content-paths';
import { arrowRightIcon } from '../../../core/ui/icons';

interface GuideState {
  blueprint: Blueprint;
  done: number;
}

@Component({
  imports: [LucideDynamicIcon, RouterLink, TranslatePipe],
  selector: 'app-guide-link',
  styleUrl: './guide-link.scss',
  templateUrl: './guide-link.html',
})
export class GuideLink {
  protected readonly arrowRightIcon = arrowRightIcon;

  protected readonly paths = inject(ContentPaths);
  private readonly progress = inject(BlueprintProgress);
  private readonly blueprints = toSignal(inject(BlueprintApi).getAll(), { initialValue: [] });

  protected readonly state = computed(() => this.pick(this.blueprints()));

  private pick(blueprints: Blueprint[]): GuideState | undefined {
    const blueprint = blueprints.find((candidate) => this.isStarted(candidate));
    if (!blueprint) {
      return undefined;
    }
    return { blueprint, done: this.progress.doneCount(blueprint) };
  }

  private isStarted(blueprint: Blueprint): boolean {
    const done = this.progress.doneCount(blueprint);
    return done > 0 && done < blueprint.steps.length;
  }
}
