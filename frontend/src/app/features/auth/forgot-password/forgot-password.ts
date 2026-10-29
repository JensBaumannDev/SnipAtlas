import { Component, computed, inject, output, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { finalize } from 'rxjs';
import { fieldErrorKey, formErrorText, toApiError } from '../../../core/api-error';
import { arrowLeftIcon } from '../../../core/icons';
import { PasswordReset } from '../../../core/password-reset';
import { hasVisibleError, injectApiError, injectFocusInvalid } from '../auth-form';

@Component({
  imports: [ReactiveFormsModule, TranslatePipe, LucideDynamicIcon],
  selector: 'app-forgot-password',
  styleUrl: './forgot-password.scss',
  templateUrl: './forgot-password.html',
  host: { class: 'auth-form' },
})
export class ForgotPassword {
  private readonly focusInvalid = injectFocusInvalid();
  private readonly passwordReset = inject(PasswordReset);

  readonly login = output<void>();

  protected readonly arrowLeftIcon = arrowLeftIcon;
  protected readonly attempted = signal(false);
  protected readonly sent = signal(false);
  protected readonly pending = signal(false);
  protected readonly form = inject(FormBuilder).nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  protected readonly error = injectApiError(this.form);
  protected readonly errorText = computed(() => formErrorText(this.error()));
  protected readonly emailServerError = computed(() => fieldErrorKey(this.error(), 'email'));

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
    this.send();
  }

  private send(): void {
    this.pending.set(true);
    this.sent.set(false);
    this.passwordReset
      .request(this.form.controls.email.value.trim())
      .pipe(finalize(() => this.pending.set(false)))
      .subscribe({
        next: () => this.sent.set(true),
        error: (error: unknown) => this.error.set(toApiError(error)),
      });
  }
}
