import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintApi } from '../../../core/blueprint-api';
import { BlueprintProgress } from '../../../core/blueprint-progress';
import { UserRequestApi } from '../../../core/user-request-api';
import { Collection } from '../../../shared/collection/collection';
import { ProgressBar } from '../../../shared/progress-bar/progress-bar';

const LATEST_REQUESTS = 2;

@Component({
  imports: [Collection, ProgressBar, RouterLink, TranslatePipe],
  selector: 'app-profile-overview',
  styleUrl: './profile-overview.scss',
  templateUrl: './profile-overview.html',
})
export class ProfileOverview {
  private readonly progress = inject(BlueprintProgress);
  private readonly blueprints = toSignal(inject(BlueprintApi).getAll(), { initialValue: [] });
  private readonly requests = toSignal(inject(UserRequestApi).getMine(), { initialValue: [] });

  protected readonly started = computed(() =>
    this.blueprints()
      .map((blueprint) => {
        const done = this.progress.doneSteps(blueprint.slug);
        return {
          blueprint,
          done: blueprint.steps.filter((step) => done.includes(step.slug)).length,
        };
      })
      .filter((item) => item.done > 0),
  );

  protected readonly latestRequests = computed(() => this.requests().slice(0, LATEST_REQUESTS));
}
