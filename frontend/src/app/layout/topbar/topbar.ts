import { Component, ElementRef, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { SettingsMenu } from '../settings-menu/settings-menu';

@Component({
  imports: [RouterLink, SettingsMenu],
  selector: 'app-topbar',
  styleUrl: './topbar.scss',
  templateUrl: './topbar.html',
  host: {
    '(document:keydown)': 'onKeydown($event)',
  },
})
export class Topbar {
  private readonly searchInput = viewChild.required<ElementRef<HTMLInputElement>>('searchInput');

  protected onKeydown(event: KeyboardEvent): void {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      this.searchInput().nativeElement.focus();
    }
  }
}
