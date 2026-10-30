import { HttpClient } from '@angular/common/http';
import { PLATFORM_ID, Service, computed, inject, signal } from '@angular/core';
import { isPlatformServer } from '@angular/common';
import { Observable, catchError, firstValueFrom, map, of, switchMap } from 'rxjs';
import type { AccentTheme } from '../user-data/preferences';

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

export interface PasswordChange {
  current: string;
  next: string;
}

export type AccountSettings = Partial<Pick<SessionUser, 'notifyByMail' | 'accent'>>;

export type AuthEvent = 'restore' | 'login' | 'logout';

const URL = '/api/auth/';

@Service()
export class Session {
  private readonly http = inject(HttpClient);
  private readonly isServer = isPlatformServer(inject(PLATFORM_ID));

  readonly user = signal<SessionUser | undefined>(undefined);
  readonly authEvent = signal<AuthEvent | undefined>(undefined);
  readonly initial = computed(() => this.user()?.email.charAt(0).toUpperCase() ?? '');

  restore(): Promise<void> {
    if (this.isServer) {
      return Promise.resolve();
    }
    const restored = this.refreshCsrf().pipe(
      switchMap(() => this.http.get<SessionUser | null>(`${URL}me/`)),
      map((user) => {
        if (user) {
          this.signIn(user, 'restore');
        }
      }),
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

  saveSettings(changes: AccountSettings): void {
    const previous = this.user();
    this.update(changes);
    this.http.patch<SessionUser>(`${URL}me/`, changes).subscribe({
      next: (user) => this.user.set(user),
      error: () => this.user.set(previous),
    });
  }

  changeEmail(credentials: Credentials): Observable<void> {
    return this.http
      .post<SessionUser>(`${URL}email/`, credentials)
      .pipe(map((user) => this.user.set(user)));
  }

  changePassword(change: PasswordChange): Observable<void> {
    return this.http
      .post<SessionUser>(`${URL}password/`, change)
      .pipe(map((user) => this.user.set(user)));
  }

  deleteAccount(password: string): Observable<void> {
    return this.http
      .post<void>(`${URL}delete-account/`, { password })
      .pipe(map(() => this.clear()));
  }

  private signIn(user: SessionUser, event: AuthEvent): void {
    this.user.set(user);
    this.authEvent.set(event);
  }
}
