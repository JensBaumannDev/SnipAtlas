import { HttpClient } from '@angular/common/http';
import { Service, computed, inject, signal } from '@angular/core';
import { Observable, catchError, firstValueFrom, map, of, switchMap } from 'rxjs';
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

export type AccountUser = Omit<SessionUser, 'favorites'>;

export interface Credentials {
  email: string;
  password: string;
}

const URL = '/api/auth/';

@Service()
export class Session {
  private readonly http = inject(HttpClient);

  readonly user = signal<SessionUser | undefined>(undefined);
  readonly initial = computed(() => this.user()?.email.charAt(0).toUpperCase() ?? '');

  restore(): Promise<void> {
    const restored = this.refreshCsrf().pipe(
      switchMap(() => this.http.get<AccountUser>(`${URL}me/`)),
      map((user) => this.signIn(user)),
      catchError(() => of(undefined)),
    );
    return firstValueFrom(restored);
  }

  refreshCsrf(): Observable<void> {
    return this.http.get<void>(`${URL}csrf/`);
  }

  login(credentials: Credentials): Observable<void> {
    return this.http
      .post<AccountUser>(`${URL}login/`, credentials)
      .pipe(map((user) => this.signIn(user)));
  }

  register(credentials: Credentials): Observable<void> {
    return this.http
      .post<AccountUser>(`${URL}register/`, credentials)
      .pipe(map((user) => this.signIn(user)));
  }

  logout(): void {
    this.clear();
    this.http.post<void>(`${URL}logout/`, null).subscribe({ error: () => undefined });
  }

  clear(): void {
    this.user.set(undefined);
  }

  update(changes: Partial<SessionUser>): void {
    this.user.update((user) => (user ? { ...user, ...changes } : user));
  }

  private signIn(user: AccountUser): void {
    this.user.set({ ...user, favorites: [] });
  }
}
