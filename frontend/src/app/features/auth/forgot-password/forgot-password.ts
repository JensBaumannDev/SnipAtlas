import { Component, computed, inject, output, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideArrowLeft } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { hasVisibleError, injectFocusInvalid } from '../auth-form';

@Component({
  imports: [ReactiveFormsModule, TranslatePipe, LucideArrowLeft],
  selector: 'app-forgot-password',
  styleUrl: './forgot-password.scss',
  templateUrl: './forgot-password.html',
  host: { class: 'auth-form' },
})
export class ForgotPassword {
  private readonly focusInvalid = injectFocusInvalid();

  readonly login = output<void>();

  protected readonly attempted = signal(false);
  protected readonly submitted = signal(false);
  protected readonly form = inject(FormBuilder).nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  private readonly values = toSignal(this.form.valueChanges, {
    initialValue: this.form.getRawValue(),
  });

  protected readonly filled = computed(() => !!this.values().email?.trim());

  protected emailError(): boolean {
    return hasVisibleError(this.form.controls.email, 'email', this.attempted());
  }

  protected submit(): void {
    this.attempted.set(true);
    if (this.form.invalid) {
      this.focusInvalid();
      return;
    }
    this.submitted.set(true);
  }
}
