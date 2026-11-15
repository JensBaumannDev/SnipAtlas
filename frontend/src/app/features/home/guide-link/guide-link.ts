import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintApi } from '../../../core/api/blueprint-api';
import { Blueprint } from '../../../core/models/blueprint';
import { BlueprintProgress } from '../../../core/user-data/blueprint-progress';

interface GuideState {
  blueprint: Blueprint;
  started: boolean;
  done: number;
}

@Component({
  imports: [RouterLink, TranslatePipe],
  selector: 'app-guide-link',
  styleUrl: './guide-link.scss',
  templateUrl: './guide-link.html',
})
export class GuideLink {
  private readonly progress = inject(BlueprintProgress);
  private readonly blueprints = toSignal(inject(BlueprintApi).getAll(), { initialValue: [] });

  protected readonly state = computed(() => this.pick(this.blueprints()));

  private pick(blueprints: Blueprint[]): GuideState | undefined {
    const started = blueprints.find((blueprint) => this.isStarted(blueprint));
    const blueprint = started ?? blueprints[0];
    if (!blueprint) {
      return undefined;
    }
    return {
      blueprint,
      started: started !== undefined,
      done: this.progress.doneCount(blueprint),
    };
  }

  private isStarted(blueprint: Blueprint): boolean {
    const done = this.progress.doneCount(blueprint);
    return done > 0 && done < blueprint.steps.length;
  }
}
