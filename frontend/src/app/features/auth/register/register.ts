import { Component, computed, inject, output, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { finalize } from 'rxjs';
import { fieldErrorKey, formErrorText, toApiError } from '../../../core/http/api-error';
import { PASSWORD_MIN_LENGTH } from '../../../core/auth/password-rules';
import { Session } from '../../../core/auth/session';
import { PasswordField } from '../../../shared/password-field/password-field';
import {
  hasVisibleError,
  injectApiError,
  injectFocusInvalid,
  injectFocusTitle,
  passwordsMatch,
} from '../auth-form';
import { ResendActivation } from '../resend-activation/resend-activation';

@Component({
  imports: [PasswordField, ReactiveFormsModule, ResendActivation, TranslatePipe],
  selector: 'app-register',
  styleUrl: './register.scss',
  templateUrl: './register.html',
  host: { class: 'auth-form' },
})
export class Register {
  private readonly focusInvalid = injectFocusInvalid();
  private readonly focusTitle = injectFocusTitle();
  private readonly session = inject(Session);

  readonly login = output<void>();

  protected readonly sentTo = signal<string | undefined>(undefined);

  protected readonly minLength = PASSWORD_MIN_LENGTH;
  protected readonly attempted = signal(false);
  protected readonly form = inject(FormBuilder).nonNullable.group(
    {
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(PASSWORD_MIN_LENGTH)]],
      repeat: ['', Validators.required],
    },
    { validators: passwordsMatch },
  );

  protected readonly pending = signal(false);
  protected readonly error = injectApiError(this.form);
  protected readonly errorText = computed(() => formErrorText(this.error()));
  protected readonly emailServerError = computed(() => fieldErrorKey(this.error(), 'email'));
  protected readonly passwordServerError = computed(() => fieldErrorKey(this.error(), 'password'));

  private readonly values = toSignal(this.form.valueChanges, {
    initialValue: this.form.getRawValue(),
  });

  protected readonly filled = computed(() => {
    const { email, password, repeat } = this.values();
    return !!email?.trim() && !!password && !!repeat;
  });

  protected emailError(): boolean {
    return hasVisibleError(this.form.controls.email, 'email', this.attempted());
  }

  protected passwordError(): boolean {
    return hasVisibleError(this.form.controls.password, 'minlength', this.attempted());
  }

  protected repeatError(): boolean {
    const control = this.form.controls.repeat;
    return (
      this.form.hasError('mismatch') && !!control.value && (this.attempted() || control.touched)
    );
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
    const { password } = this.form.getRawValue();
    const email = this.form.controls.email.value.trim();
    this.pending.set(true);
    this.error.set(undefined);
    this.session
      .register({ email, password })
      .pipe(finalize(() => this.pending.set(false)))
      .subscribe({
        next: () => this.showSent(email),
        error: (error: unknown) => {
          this.error.set(toApiError(error));
          this.focusInvalid();
        },
      });
  }

  private showSent(email: string): void {
    this.sentTo.set(email);
    this.focusTitle();
  }
}
