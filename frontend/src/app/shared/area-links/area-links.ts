import { Component } from '@angular/core';
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
  imports: [RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-area-links',
  styleUrl: './area-links.scss',
  templateUrl: './area-links.html',
})
export class AreaLinks {
  protected readonly areas = AREAS;
}
