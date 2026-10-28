import { Component, computed, input, model } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { chevronDownIcon } from '../../core/icons';

@Component({
  imports: [LucideDynamicIcon],
  selector: 'app-disclosure',
  styleUrl: './disclosure.scss',
  templateUrl: './disclosure.html',
})
export class Disclosure {
  readonly anchor = input.required<string>();
  readonly level = input<2 | 3 | 4>(3);
  readonly expanded = model(false);

  protected readonly chevronDownIcon = chevronDownIcon;
  protected readonly bodyId = computed(() => `${this.anchor()}-body`);

  protected toggle(): void {
    this.expanded.update((expanded) => !expanded);
  }
}
