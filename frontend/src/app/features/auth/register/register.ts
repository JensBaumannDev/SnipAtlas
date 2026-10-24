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
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { Session } from '../../../core/session';

const PASSWORD_MIN_LENGTH = 8;

function passwordsMatch(group: AbstractControl): ValidationErrors | null {
  const { password, repeat } = group.getRawValue() as { password: string; repeat: string };
  return password === repeat ? null : { mismatch: true };
}

@Component({
  imports: [ReactiveFormsModule, TranslatePipe],
  selector: 'app-register',
  styleUrl: './register.scss',
  templateUrl: './register.html',
  host: { class: 'auth-form' },
})
export class Register {
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly injector = inject(Injector);
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
    const control = this.form.controls.email;
    return control.hasError('email') && (this.attempted() || control.touched);
  }

  protected passwordError(): boolean {
    const control = this.form.controls.password;
    return control.hasError('minlength') && (this.attempted() || control.touched);
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
