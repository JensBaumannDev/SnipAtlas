import { Component, computed, inject, output, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { PASSWORD_MIN_LENGTH } from '../../../core/password-rules';
import { Session } from '../../../core/session';
import { PasswordField } from '../../../shared/password-field/password-field';
import { hasVisibleError, injectFocusInvalid } from '../auth-form';

function passwordsMatch(group: AbstractControl): ValidationErrors | null {
  const { password, repeat } = group.getRawValue() as { password: string; repeat: string };
  return password === repeat ? null : { mismatch: true };
}

@Component({
  imports: [PasswordField, ReactiveFormsModule, TranslatePipe],
  selector: 'app-register',
  styleUrl: './register.scss',
  templateUrl: './register.html',
  host: { class: 'auth-form' },
})
export class Register {
  private readonly focusInvalid = injectFocusInvalid();
  private readonly session = inject(Session);

  readonly done = output<void>();
  readonly login = output<void>();

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
    this.session.login(this.form.controls.email.value);
    this.done.emit();
  }
}
