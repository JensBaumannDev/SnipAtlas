import { Location } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { finalize } from 'rxjs';
import { ApiError, fieldErrorKey, formErrorText, toApiError } from '../../../core/http/api-error';
import { LoginDialog } from '../../../core/auth/login-dialog';
import { PASSWORD_MIN_LENGTH } from '../../../core/auth/password-rules';
import { PasswordReset } from '../../../core/auth/password-reset';
import { Session } from '../../../core/auth/session';
import { PasswordField } from '../../../shared/password-field/password-field';
import { hasVisibleError, injectApiError, injectFocusInvalid, passwordsMatch } from '../auth-form';

type ResetStatus = 'form' | 'done' | 'invalid';

interface ResetLink {
  uid: string;
  token: string;
}

function readLink(route: ActivatedRoute, location: Location): ResetLink | undefined {
  const params = route.snapshot.queryParamMap;
  const uid = params.get('uid');
  const token = params.get('token');
  location.replaceState(location.path().split('?')[0]);
  return uid && token ? { uid, token } : undefined;
}

@Component({
  imports: [PasswordField, ReactiveFormsModule, TranslatePipe],
  selector: 'app-reset-password',
  styleUrl: './reset-password.scss',
  templateUrl: './reset-password.html',
})
export class ResetPassword {
  private readonly focusInvalid = injectFocusInvalid();
  private readonly loginDialog = inject(LoginDialog);
  private readonly passwordReset = inject(PasswordReset);
  private readonly session = inject(Session);
  private readonly link = readLink(inject(ActivatedRoute), inject(Location));

  protected readonly minLength = PASSWORD_MIN_LENGTH;
  protected readonly status = signal<ResetStatus>(this.link ? 'form' : 'invalid');
  protected readonly attempted = signal(false);
  protected readonly pending = signal(false);
  protected readonly form = inject(FormBuilder).nonNullable.group(
    {
      password: ['', [Validators.required, Validators.minLength(PASSWORD_MIN_LENGTH)]],
      repeat: ['', Validators.required],
    },
    { validators: passwordsMatch },
  );

  protected readonly error = injectApiError(this.form);
  protected readonly errorText = computed(() => formErrorText(this.error()));
  protected readonly passwordServerError = computed(() => fieldErrorKey(this.error(), 'password'));

  private readonly values = toSignal(this.form.valueChanges, {
    initialValue: this.form.getRawValue(),
  });

  protected readonly filled = computed(() => {
    const { password, repeat } = this.values();
    return !!password && !!repeat;
  });

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
    if (this.form.invalid || !this.link) {
      this.focusInvalid();
      return;
    }
    this.send(this.link);
  }

  protected login(): void {
    this.loginDialog.open();
  }

  private send(link: ResetLink): void {
    this.pending.set(true);
    this.passwordReset
      .confirm({ ...link, password: this.form.controls.password.value })
      .pipe(finalize(() => this.pending.set(false)))
      .subscribe({
        next: () => this.finish(),
        error: (error: unknown) => this.fail(toApiError(error)),
      });
  }

  private finish(): void {
    this.session.clear();
    this.status.set('done');
  }

  private fail(error: ApiError): void {
    if (error.code === 'invalid_link') {
      this.status.set('invalid');
      return;
    }
    this.error.set(error);
    this.focusInvalid();
  }
}
