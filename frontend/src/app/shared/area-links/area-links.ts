import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon, LucideIconData } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { bookAIcon, bookTextIcon, botIcon, routeIcon, terminalIcon, triangleAlertIcon } from '../../core/ui/icons';

interface Area {
  path: string;
  label: string;
  description: string;
  icon: LucideIconData;
}

const AREAS: Area[] = [
  {
    path: '/begriffe',
    label: 'nav.glossary',
    description: 'home.areas.glossary',
    icon: bookAIcon,
  },
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
  {
    path: '/ki-coding',
    label: 'nav.ai',
    description: 'home.areas.ai',
    icon: botIcon,
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
