import { Component, computed, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-progress-bar',
  styleUrl: './progress-bar.scss',
  templateUrl: './progress-bar.html',
})
export class ProgressBar {
  readonly done = input.required<number>();
  readonly total = input.required<number>();
  readonly label = input.required<string>();

  protected readonly percent = computed(() =>
    this.total() ? Math.round((this.done() / this.total()) * 100) : 0,
  );
  protected readonly complete = computed(() => this.total() > 0 && this.done() === this.total());
}
