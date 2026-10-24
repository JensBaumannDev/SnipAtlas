import { Component, ElementRef, inject, signal } from '@angular/core';
import { LucideEye, LucideEyeOff } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe, LucideEye, LucideEyeOff],
  selector: 'app-password-field',
  styleUrl: './password-field.scss',
  templateUrl: './password-field.html',
})
export class PasswordField {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;

  protected readonly visible = signal(false);

  protected toggle(): void {
    const input = this.host.querySelector('input');
    if (!input) {
      return;
    }
    this.visible.update((visible) => !visible);
    input.type = this.visible() ? 'text' : 'password';
  }
}
