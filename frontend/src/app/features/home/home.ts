import { DatePipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
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
import { NewsApi } from '../../core/news-api';

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
  imports: [DatePipe, RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-home',
  styleUrl: './home.scss',
  templateUrl: './home.html',
})
export class Home {
  protected readonly areas = AREAS;
  protected readonly news = toSignal(inject(NewsApi).getLatest(), { initialValue: [] });
}
