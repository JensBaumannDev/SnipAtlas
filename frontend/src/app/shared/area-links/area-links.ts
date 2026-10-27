import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon, LucideIconData } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { bookTextIcon, routeIcon, terminalIcon, triangleAlertIcon } from '../../core/icons';

interface Area {
  path: string;
  label: string;
  description: string;
  icon: LucideIconData;
}

const AREAS: Area[] = [
  {
    path: '/befehle',
    label: 'nav.commands',
    description: 'home.areas.commands',
    icon: terminalIcon,
  },
  {
    path: '/grundlagen',
    label: 'nav.concepts',
    description: 'home.areas.concepts',
    icon: bookTextIcon,
  },
  {
    path: '/anleitungen',
    label: 'nav.blueprints',
    description: 'home.areas.blueprints',
    icon: routeIcon,
  },
  {
    path: '/fehler',
    label: 'nav.debugging',
    description: 'home.areas.debugging',
    icon: triangleAlertIcon,
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
