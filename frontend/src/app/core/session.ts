import { HttpClient } from '@angular/common/http';
import { Service, computed, inject, signal } from '@angular/core';
import { Observable, catchError, firstValueFrom, map, of, switchMap } from 'rxjs';
import type { AccentTheme } from './preferences';

export interface SessionUser {
  email: string;
  since: string;
  notifyByMail: boolean;
  accent: AccentTheme;
}

export interface Credentials {
  email: string;
  password: string;
}

export type AuthEvent = 'restore' | 'login' | 'logout';

const URL = '/api/auth/';

@Service()
export class Session {
  private readonly http = inject(HttpClient);

  readonly user = signal<SessionUser | undefined>(undefined);
  readonly authEvent = signal<AuthEvent | undefined>(undefined);
  readonly initial = computed(() => this.user()?.email.charAt(0).toUpperCase() ?? '');

  restore(): Promise<void> {
    const restored = this.refreshCsrf().pipe(
      switchMap(() => this.http.get<SessionUser>(`${URL}me/`)),
      map((user) => this.signIn(user, 'restore')),
      catchError(() => of(undefined)),
    );
    return firstValueFrom(restored);
  }

  refreshCsrf(): Observable<void> {
    return this.http.get<void>(`${URL}csrf/`);
  }

  login(credentials: Credentials): Observable<void> {
    return this.http
      .post<SessionUser>(`${URL}login/`, credentials)
      .pipe(map((user) => this.signIn(user, 'login')));
  }

  register(credentials: Credentials): Observable<void> {
    return this.http
      .post<SessionUser>(`${URL}register/`, credentials)
      .pipe(map((user) => this.signIn(user, 'login')));
  }

  logout(): void {
    this.clear();
    this.http.post<void>(`${URL}logout/`, null).subscribe({ error: () => undefined });
  }

  clear(): void {
    if (this.user()) {
      this.authEvent.set('logout');
    }
    this.user.set(undefined);
  }

  update(changes: Partial<SessionUser>): void {
    this.user.update((user) => (user ? { ...user, ...changes } : user));
  }

  private signIn(user: SessionUser, event: AuthEvent): void {
    this.user.set(user);
    this.authEvent.set(event);
  }
}
