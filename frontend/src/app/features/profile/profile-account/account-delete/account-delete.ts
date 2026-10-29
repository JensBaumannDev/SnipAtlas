import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { finalize } from 'rxjs';
import { formErrorText, toApiError } from '../../../../core/http/api-error';
import { Session } from '../../../../core/auth/session';
import { PasswordField } from '../../../../shared/password-field/password-field';
import { injectApiError } from '../../../auth/auth-form';

@Component({
  imports: [PasswordField, ReactiveFormsModule, TranslatePipe],
  selector: 'app-account-delete',
  styleUrl: './account-delete.scss',
  templateUrl: './account-delete.html',
})
export class AccountDelete {
  private readonly router = inject(Router);
  private readonly session = inject(Session);

  protected readonly confirming = signal(false);
  protected readonly pending = signal(false);
  protected readonly form = inject(FormBuilder).nonNullable.group({
    password: ['', Validators.required],
  });

  protected readonly error = injectApiError(this.form);
  protected readonly errorText = computed(() => formErrorText(this.error()));

  protected cancel(): void {
    this.form.reset();
    this.confirming.set(false);
  }

  protected submit(): void {
    if (this.form.invalid) {
      return;
    }
    this.pending.set(true);
    this.session
      .deleteAccount(this.form.controls.password.value)
      .pipe(finalize(() => this.pending.set(false)))
      .subscribe({
        next: () => this.router.navigateByUrl('/'),
        error: (error: unknown) => this.error.set(toApiError(error)),
      });
  }
}
