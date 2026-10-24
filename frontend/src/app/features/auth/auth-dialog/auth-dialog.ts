import { DialogRef } from '@angular/cdk/dialog';
import { Component, ElementRef, Injector, afterNextRender, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { LucideX } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { ForgotPassword } from '../forgot-password/forgot-password';
import { Login } from '../login/login';
import { Register } from '../register/register';

export type AuthView = 'login' | 'register' | 'forgot';

@Component({
  imports: [ForgotPassword, Login, Register, TranslatePipe, LucideX],
  selector: 'app-auth-dialog',
  styleUrl: './auth-dialog.scss',
  templateUrl: './auth-dialog.html',
  host: {
    '[class.auth-dialog--closing]': 'closing()',
  },
})
export class AuthDialog {
  private readonly dialogRef = inject(DialogRef);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly injector = inject(Injector);

  protected readonly view = signal<AuthView>('login');
  protected readonly closing = signal(false);

  constructor() {
    this.dialogRef.backdropClick.pipe(takeUntilDestroyed()).subscribe(() => this.close());
    this.dialogRef.keydownEvents.pipe(takeUntilDestroyed()).subscribe((event) => {
      if (event.key === 'Escape') {
        this.close();
      }
    });
  }

  protected show(view: AuthView): void {
    this.view.set(view);
    afterNextRender(() => this.host.querySelector<HTMLElement>('input')?.focus(), {
      injector: this.injector,
    });
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
