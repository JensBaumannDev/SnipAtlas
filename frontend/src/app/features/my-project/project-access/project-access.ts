import { Component, ElementRef, Injector, afterNextRender, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Session } from '../../../core/auth/session';
import type { AuthView } from '../../auth/auth-dialog/auth-dialog';
import { ForgotPassword } from '../../auth/forgot-password/forgot-password';
import { Login } from '../../auth/login/login';
import { Register } from '../../auth/register/register';

@Component({
  imports: [ForgotPassword, Login, Register, RouterOutlet, TranslatePipe],
  selector: 'app-project-access',
  styleUrl: './project-access.scss',
  templateUrl: './project-access.html',
})
export class ProjectAccess {
  protected readonly session = inject(Session);
  private readonly injector = inject(Injector);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  protected readonly view = signal<AuthView | 'intro'>('intro');
  protected readonly phases = [
    'prepare',
    'backend',
    'frontend',
    'connect',
    'docker',
    'postgres',
    'login',
    'server',
    'online',
  ] as const;

  protected show(view: AuthView): void {
    this.view.set(view);
    afterNextRender(() => this.host.nativeElement.querySelector<HTMLElement>('#auth-title')?.focus(), {
      injector: this.injector,
    });
  }
}
