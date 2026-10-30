import { Service, signal } from '@angular/core';

@Service()
export class Notifications {
  readonly message = signal<string | undefined>(undefined);
  private timeout: ReturnType<typeof setTimeout> | undefined;

  show(message: string): void {
    this.message.set(message);
    clearTimeout(this.timeout);
    this.timeout = setTimeout(() => this.dismiss(), 4000);
  }

  dismiss(): void {
    clearTimeout(this.timeout);
    this.timeout = undefined;
    this.message.set(undefined);
  }
}
