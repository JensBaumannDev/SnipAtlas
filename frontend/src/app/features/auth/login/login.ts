import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  inject,
  output,
  signal,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { Session } from '../../../core/session';
import { PasswordField } from '../../../shared/password-field/password-field';

@Component({
  imports: [PasswordField, ReactiveFormsModule, TranslatePipe],
  selector: 'app-login',
  styleUrl: './login.scss',
  templateUrl: './login.html',
  host: { class: 'auth-form' },
})
export class Login {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly injector = inject(Injector);
  private readonly session = inject(Session);

  readonly done = output<void>();
  readonly forgot = output<void>();
  readonly register = output<void>();

  protected readonly attempted = signal(false);
  protected readonly form = inject(FormBuilder).nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  private readonly values = toSignal(this.form.valueChanges, {
    initialValue: this.form.getRawValue(),
  });

  protected readonly filled = computed(() => {
    const { email, password } = this.values();
    return !!email?.trim() && !!password;
  });

  protected emailError(): boolean {
    const control = this.form.controls.email;
    return control.hasError('email') && (this.attempted() || control.touched);
  }

  protected submit(): void {
    this.attempted.set(true);
    if (this.form.invalid) {
      afterNextRender(
        () => this.host.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus(),
        { injector: this.injector },
      );
      return;
    }
    this.session.login(this.form.controls.email.value);
    this.done.emit();
  }
}
