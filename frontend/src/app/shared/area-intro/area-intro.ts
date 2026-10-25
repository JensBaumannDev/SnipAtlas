import { Component, input } from '@angular/core';
import { LucideDynamicIcon, LucideIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe, LucideDynamicIcon],
  selector: 'app-area-intro',
  styleUrl: './area-intro.scss',
  templateUrl: './area-intro.html',
})
export class AreaIntro {
  readonly icon = input.required<LucideIcon>();
  readonly title = input.required<string>();
  readonly lead = input.required<string>();
  readonly summary = input<string>();
}
