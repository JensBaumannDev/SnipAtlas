import { Service, computed, signal } from '@angular/core';

export interface SessionUser {
  email: string;
}

@Service()
export class Session {
  readonly user = signal<SessionUser | undefined>(undefined);
  readonly initial = computed(() => this.user()?.email.charAt(0).toUpperCase() ?? '');

  login(email: string): void {
    this.user.set({ email: email.trim() });
  }

  logout(): void {
    this.user.set(undefined);
  }
}
