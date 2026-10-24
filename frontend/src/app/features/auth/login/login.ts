import { DialogRef } from '@angular/cdk/dialog';
import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideX } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [ReactiveFormsModule, TranslatePipe, LucideX],
  selector: 'app-login',
  styleUrl: './login.scss',
  templateUrl: './login.html',
  host: {
    '[class.login--closing]': 'closing()',
  },
})
export class Login {
  private readonly dialogRef = inject(DialogRef);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly injector = inject(Injector);

  protected readonly closing = signal(false);
  protected readonly attempted = signal(false);
  protected readonly submitted = signal(false);
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

  constructor() {
    this.dialogRef.backdropClick.pipe(takeUntilDestroyed()).subscribe(() => this.close());
    this.dialogRef.keydownEvents.pipe(takeUntilDestroyed()).subscribe((event) => {
      if (event.key === 'Escape') {
        this.close();
      }
    });
  }

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
    this.submitted.set(true);
  }

  protected close(): void {
    if (this.closing()) {
      return;
    }
    this.closing.set(true);
    afterNextRender(
      async () => {
        await Promise.all(this.host.getAnimations().map((animation) => animation.finished));
        this.dialogRef.close();
      },
      { injector: this.injector },
    );
  }
}
