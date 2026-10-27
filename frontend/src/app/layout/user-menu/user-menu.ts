import { Component, ElementRef, inject, output, signal, viewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { logOutIcon, messageSquareIcon, settingsIcon, userIcon } from '../../core/icons';
import { Session } from '../../core/session';

@Component({
  imports: [RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-user-menu',
  styleUrl: './user-menu.scss',
  templateUrl: './user-menu.html',
  host: {
    '(document:click)': 'onDocumentClick($event)',
    '(keydown.escape)': 'closeAndFocus()',
  },
})
export class UserMenu {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly trigger = viewChild.required<ElementRef<HTMLButtonElement>>('trigger');

  readonly loggedOut = output<void>();

  protected readonly session = inject(Session);
  protected readonly logOutIcon = logOutIcon;
  protected readonly messageSquareIcon = messageSquareIcon;
  protected readonly settingsIcon = settingsIcon;
  protected readonly userIcon = userIcon;
  protected readonly open = signal(false);

  focus(): void {
    this.trigger().nativeElement.focus();
  }

  protected toggle(): void {
    this.open.update((open) => !open);
  }

  protected close(): void {
    this.open.set(false);
  }

  protected closeAndFocus(): void {
    if (this.open()) {
      this.close();
      this.focus();
    }
  }

  protected logout(): void {
    this.close();
    this.session.logout();
    this.loggedOut.emit();
  }

  protected onDocumentClick(event: MouseEvent): void {
    if (event.target instanceof Node && !this.host.contains(event.target)) {
      this.close();
    }
  }
}
