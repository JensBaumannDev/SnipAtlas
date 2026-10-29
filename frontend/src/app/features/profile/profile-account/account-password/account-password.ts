import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { finalize } from 'rxjs';
import { fieldErrorKey, formErrorText, toApiError } from '../../../../core/http/api-error';
import { PASSWORD_MIN_LENGTH } from '../../../../core/auth/password-rules';
import { Session } from '../../../../core/auth/session';
import { PasswordField } from '../../../../shared/password-field/password-field';
import { hasVisibleError, injectApiError, injectFocusInvalid } from '../../../auth/auth-form';

@Component({
  imports: [PasswordField, ReactiveFormsModule, TranslatePipe],
  selector: 'app-account-password',
  styleUrl: './account-password.scss',
  templateUrl: './account-password.html',
})
export class AccountPassword {
  private readonly focusInvalid = injectFocusInvalid();
  private readonly session = inject(Session);

  protected readonly minLength = PASSWORD_MIN_LENGTH;
  protected readonly saved = signal(false);
  protected readonly pending = signal(false);
  protected readonly form = inject(FormBuilder).nonNullable.group({
    current: ['', Validators.required],
    next: ['', [Validators.required, Validators.minLength(PASSWORD_MIN_LENGTH)]],
  });

  protected readonly error = injectApiError(this.form);
  protected readonly errorText = computed(() => formErrorText(this.error()));
  protected readonly nextServerError = computed(() => fieldErrorKey(this.error(), 'next'));

  private readonly values = toSignal(this.form.valueChanges, {
    initialValue: this.form.getRawValue(),
  });

  protected readonly filled = computed(() => {
    const { current, next } = this.values();
    return !!current && !!next;
  });

  protected nextError(): boolean {
    return hasVisibleError(this.form.controls.next, 'minlength', false);
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
    this.pending.set(true);
    this.saved.set(false);
    this.session
      .changePassword(this.form.getRawValue())
      .pipe(finalize(() => this.pending.set(false)))
      .subscribe({
        next: () => this.done(),
        error: (error: unknown) => {
          this.error.set(toApiError(error));
          this.focusInvalid();
        },
      });
  }

  private done(): void {
    this.form.reset();
    this.saved.set(true);
  }
}
