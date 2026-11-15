import { Component, computed, inject, input, signal } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { finalize } from 'rxjs';
import { EmailConfirmation } from '../../../core/auth/email-confirmation';
import { ApiError, formErrorText, toApiError } from '../../../core/http/api-error';

@Component({
  imports: [TranslatePipe],
  selector: 'app-resend-activation',
  styleUrl: './resend-activation.scss',
  templateUrl: './resend-activation.html',
})
export class ResendActivation {
  private readonly emailConfirmation = inject(EmailConfirmation);

  readonly email = input.required<string>();

  protected readonly sent = signal(false);
  protected readonly pending = signal(false);
  protected readonly error = signal<ApiError | undefined>(undefined);
  protected readonly errorText = computed(() => formErrorText(this.error()));

  protected send(): void {
    this.pending.set(true);
    this.sent.set(false);
    this.error.set(undefined);
    this.emailConfirmation
      .resendActivation(this.email())
      .pipe(finalize(() => this.pending.set(false)))
      .subscribe({
        next: () => this.sent.set(true),
        error: (error: unknown) => this.error.set(toApiError(error)),
      });
  }
}
