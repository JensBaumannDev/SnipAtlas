import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { finalize } from 'rxjs';
import { fieldErrorKey, formErrorText, toApiError } from '../../../../core/http/api-error';
import { Session } from '../../../../core/auth/session';
import { PasswordField } from '../../../../shared/password-field/password-field';
import { hasVisibleError, injectApiError, injectFocusInvalid } from '../../../auth/auth-form';

@Component({
  imports: [PasswordField, ReactiveFormsModule, TranslatePipe],
  selector: 'app-account-email',
  styleUrl: './account-email.scss',
  templateUrl: './account-email.html',
})
export class AccountEmail {
  private readonly focusInvalid = injectFocusInvalid();
  private readonly session = inject(Session);

  protected readonly saved = signal(false);
  protected readonly pending = signal(false);
  protected readonly form = inject(FormBuilder).nonNullable.group({
    email: [this.session.user()?.email ?? '', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  protected readonly error = injectApiError(this.form);
  protected readonly errorText = computed(() => formErrorText(this.error()));
  protected readonly emailServerError = computed(() => fieldErrorKey(this.error(), 'email'));

  private readonly values = toSignal(this.form.valueChanges, {
    initialValue: this.form.getRawValue(),
  });

  protected readonly filled = computed(() => {
    const { email = '', password } = this.values();
    return !!email.trim() && email.trim() !== this.session.user()?.email && !!password;
  });

  protected emailError(): boolean {
    return hasVisibleError(this.form.controls.email, 'email', false);
  }

  protected submit(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid) {
      this.focusInvalid();
      return;
    }
    this.send();
  }

  private send(): void {
    const { email, password } = this.form.getRawValue();
    this.pending.set(true);
    this.saved.set(false);
    this.session
      .changeEmail({ email: email.trim(), password })
      .pipe(finalize(() => this.pending.set(false)))
      .subscribe({
        next: () => this.done(),
        error: (error: unknown) => this.error.set(toApiError(error)),
      });
  }

  private done(): void {
    this.form.controls.password.reset();
    this.saved.set(true);
  }
}
