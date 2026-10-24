import { Service, computed, signal } from '@angular/core';
import type { AccentTheme } from './preferences';

export interface Favorite {
  topic: string;
  subtopic: string;
  slug: string;
  title: string;
}

export interface SessionUser {
  email: string;
  since: string;
  notifyByMail: boolean;
  accent: AccentTheme;
  favorites: Favorite[];
}

@Service()
export class Session {
  readonly user = signal<SessionUser | undefined>(undefined);
  readonly initial = computed(() => this.user()?.email.charAt(0).toUpperCase() ?? '');

  login(email: string): void {
    this.user.set({
      email: email.trim(),
      since: new Date().toISOString().slice(0, 10),
      notifyByMail: true,
      accent: 'blue',
      favorites: [],
    });
  }

  logout(): void {
    this.user.set(undefined);
  }

  update(changes: Partial<SessionUser>): void {
    this.user.update((user) => (user ? { ...user, ...changes } : user));
  }
}
