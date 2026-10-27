import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import {
  bookAIcon,
  bookTextIcon,
  houseIcon,
  messageSquarePlusIcon,
  routeIcon,
  settingsIcon,
  terminalIcon,
  triangleAlertIcon,
} from '../../core/icons';

@Component({
  imports: [RouterLink, RouterLinkActive, TranslatePipe, LucideDynamicIcon],
  selector: 'app-rail',
  styleUrl: './rail.scss',
  templateUrl: './rail.html',
})
export class Rail {
  protected readonly bookAIcon = bookAIcon;
  protected readonly bookTextIcon = bookTextIcon;
  protected readonly houseIcon = houseIcon;
  protected readonly messageSquarePlusIcon = messageSquarePlusIcon;
  protected readonly routeIcon = routeIcon;
  protected readonly settingsIcon = settingsIcon;
  protected readonly terminalIcon = terminalIcon;
  protected readonly triangleAlertIcon = triangleAlertIcon;
}
