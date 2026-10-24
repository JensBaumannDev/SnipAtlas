import { DatePipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintApi } from '../../core/blueprint-api';
import { BlueprintProgress } from '../../core/blueprint-progress';
import { NewsApi } from '../../core/news-api';
import { Preferences } from '../../core/preferences';
import { AreaLinks } from '../../shared/area-links/area-links';
import { Collection } from '../../shared/collection/collection';
import { ProgressBar } from '../../shared/progress-bar/progress-bar';

@Component({
  imports: [AreaLinks, Collection, DatePipe, ProgressBar, RouterLink, TranslatePipe],
  selector: 'app-home',
  styleUrl: './home.scss',
  templateUrl: './home.html',
})
export class Home {
  protected readonly language = inject(Preferences).language;
  protected readonly news = toSignal(inject(NewsApi).getLatest(), { initialValue: [] });

  private readonly progress = inject(BlueprintProgress);
  private readonly blueprints = toSignal(inject(BlueprintApi).getAll(), { initialValue: [] });

  protected readonly current = computed(() =>
    this.blueprints()
      .map((blueprint) => ({ blueprint, done: this.progress.doneCount(blueprint) }))
      .find((item) => item.done > 0 && item.done < item.blueprint.steps.length),
  );
}
