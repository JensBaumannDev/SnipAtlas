import { CdkConnectedOverlay, CdkOverlayOrigin, ConnectedPosition } from '@angular/cdk/overlay';
import { Component, ElementRef, Injector, afterNextRender, inject, signal, viewChild } from '@angular/core';
import { OperatingSystem, Preferences, ThemeMode } from '../../core/preferences';

interface Option<T> {
  value: T;
  label: string;
}

@Component({
  imports: [CdkOverlayOrigin, CdkConnectedOverlay],
  selector: 'app-settings-menu',
  styleUrl: './settings-menu.scss',
  templateUrl: './settings-menu.html',
})
export class SettingsMenu {
  protected readonly preferences = inject(Preferences);
  private readonly injector = inject(Injector);
  private readonly trigger = viewChild.required<ElementRef<HTMLButtonElement>>('triggerButton');
  private readonly panel = viewChild<ElementRef<HTMLElement>>('panel');

  protected readonly isOpen = signal(false);

  protected readonly positions: ConnectedPosition[] = [
    { originX: 'end', originY: 'bottom', overlayX: 'end', overlayY: 'top', offsetY: 8 },
  ];

  protected readonly themeOptions: Option<ThemeMode>[] = [
    { value: 'light', label: 'Hell' },
    { value: 'system', label: 'System' },
    { value: 'dark', label: 'Dunkel' },
  ];

  protected readonly osOptions: Option<OperatingSystem>[] = [
    { value: 'win', label: 'Windows' },
    { value: 'unix', label: 'Linux / Mac' },
  ];

  protected toggle(): void {
    this.isOpen.update((open) => !open);
  }

  protected close(restoreFocus = false): void {
    this.isOpen.set(false);
    if (restoreFocus) {
      this.trigger().nativeElement.focus();
    }
  }

  protected onOutsideClick(event: MouseEvent): void {
    if (!this.trigger().nativeElement.contains(event.target as Node)) {
      this.close();
    }
  }

  protected onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault();
      this.close(true);
    }
  }

  protected onFocusOut(event: FocusEvent): void {
    const next = event.relatedTarget as Node | null;
    const panel = this.panel()?.nativeElement;
    if (next && !panel?.contains(next) && !this.trigger().nativeElement.contains(next)) {
      this.close();
    }
  }

  protected focusSelected(): void {
    afterNextRender(
      () => this.panel()?.nativeElement.querySelector<HTMLInputElement>('input:checked')?.focus(),
      { injector: this.injector },
    );
  }
}
