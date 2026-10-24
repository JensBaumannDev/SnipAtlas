import { Component, DOCUMENT, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { BlueprintProgress } from '../../../core/blueprint-progress';
import { PASSWORD_MIN_LENGTH } from '../../../core/password-rules';
import { Session } from '../../../core/session';
import { UserRequestApi } from '../../../core/user-request-api';
import { PasswordField } from '../../../shared/password-field/password-field';

const EXPORT_FILE = 'snipatlas-daten.json';

@Component({
  imports: [PasswordField, ReactiveFormsModule, TranslatePipe],
  selector: 'app-profile-account',
  styleUrl: './profile-account.scss',
  templateUrl: './profile-account.html',
})
export class ProfileAccount {
  private readonly document = inject(DOCUMENT);
  private readonly router = inject(Router);
  private readonly session = inject(Session);
  private readonly progress = inject(BlueprintProgress);
  private readonly requests = toSignal(inject(UserRequestApi).getMine(), { initialValue: [] });
  private readonly formBuilder = inject(FormBuilder).nonNullable;

  protected readonly minLength = PASSWORD_MIN_LENGTH;
  protected readonly emailSaved = signal(false);
  protected readonly passwordSent = signal(false);
  protected readonly confirmDelete = signal(false);

  protected readonly emailForm = this.formBuilder.group({
    email: [this.session.user()?.email ?? '', [Validators.required, Validators.email]],
  });

  protected readonly passwordForm = this.formBuilder.group({
    current: ['', Validators.required],
    next: ['', [Validators.required, Validators.minLength(PASSWORD_MIN_LENGTH)]],
  });

  private readonly emailValue = toSignal(this.emailForm.controls.email.valueChanges, {
    initialValue: this.emailForm.controls.email.value,
  });

  private readonly passwordValues = toSignal(this.passwordForm.valueChanges, {
    initialValue: this.passwordForm.getRawValue(),
  });

  protected readonly emailChanged = computed(
    () =>
      this.emailValue().trim() !== '' && this.emailValue().trim() !== this.session.user()?.email,
  );

  protected readonly passwordFilled = computed(() => {
    const { current, next } = this.passwordValues();
    return !!current && !!next;
  });

  protected emailError(): boolean {
    const control = this.emailForm.controls.email;
    return control.hasError('email') && control.touched;
  }

  protected passwordError(): boolean {
    const control = this.passwordForm.controls.next;
    return control.hasError('minlength') && control.touched;
  }

  protected saveEmail(): void {
    this.emailForm.markAllAsTouched();
    if (this.emailForm.invalid) {
      return;
    }
    this.session.update({ email: this.emailForm.controls.email.value.trim() });
    this.emailSaved.set(true);
  }

  protected changePassword(): void {
    this.passwordForm.markAllAsTouched();
    if (this.passwordForm.invalid) {
      return;
    }
    this.passwordSent.set(true);
  }

  protected download(): void {
    const window = this.document.defaultView;
    if (!window) {
      return;
    }
    const data = {
      account: this.session.user(),
      progress: this.progress.done(),
      requests: this.requests(),
    };
    const url = window.URL.createObjectURL(
      new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }),
    );
    const link = this.document.createElement('a');
    link.href = url;
    link.download = EXPORT_FILE;
    link.click();
    window.setTimeout(() => window.URL.revokeObjectURL(url));
  }

  protected logout(): void {
    this.session.logout();
    this.router.navigateByUrl('/');
  }

  protected deleteAccount(): void {
    this.session.logout();
    this.router.navigateByUrl('/');
  }
}
