import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon, LucideIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';

export interface AreaHint {
  icon: LucideIcon;
  title: string;
  text: string;
  link?: { label: string; path: string };
}

@Component({
  imports: [RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-area-intro',
  styleUrl: './area-intro.scss',
  templateUrl: './area-intro.html',
})
export class AreaIntro {
  readonly title = input.required<string>();
  readonly lead = input.required<string>();
  readonly summary = input<string>();
  readonly hints = input.required<readonly AreaHint[]>();
}
