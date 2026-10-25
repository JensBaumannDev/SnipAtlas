import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import {
  LucideBookA,
  LucideBookText,
  LucideHouse,
  LucideMessageSquarePlus,
  LucideRoute,
  LucideSettings,
  LucideTerminal,
  LucideTriangleAlert,
} from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [
    RouterLink,
    RouterLinkActive,
    TranslatePipe,
    LucideHouse,
    LucideBookA,
    LucideTerminal,
    LucideBookText,
    LucideRoute,
    LucideTriangleAlert,
    LucideSettings,
    LucideMessageSquarePlus,
  ],
  selector: 'app-rail',
  styleUrl: './rail.scss',
  templateUrl: './rail.html',
})
export class Rail {}
