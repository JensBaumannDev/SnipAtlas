import type { DialogRef } from '@angular/cdk/dialog';
import { Injector, Service, inject } from '@angular/core';
import type { AuthDialog } from '../../features/auth/auth-dialog/auth-dialog';

@Service()
export class LoginDialog {
  private readonly injector = inject(Injector);

  async open(): Promise<DialogRef<unknown, AuthDialog>> {
    const [{ Dialog }, { AuthDialog }] = await Promise.all([
      import('@angular/cdk/dialog'),
      import('../../features/auth/auth-dialog/auth-dialog'),
    ]);
    return this.injector.get(Dialog).open(AuthDialog, {
      ariaLabelledBy: 'auth-title',
      autoFocus: '#auth-title',
      backdropClass: 'dialog-backdrop',
      disableClose: true,
    });
  }
}
