import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable, switchMap } from 'rxjs';
import type { MailLink } from './link';
import { Session } from './session';

const URL = '/api/auth/';

@Service()
export class EmailConfirmation {
  private readonly http = inject(HttpClient);
  private readonly session = inject(Session);

  resendActivation(email: string): Observable<void> {
    return this.http.post<void>(`${URL}activate/resend/`, { email });
  }

  confirmEmail(link: MailLink): Observable<void> {
    return this.http
      .post<void>(`${URL}email/confirm/`, link)
      .pipe(switchMap(() => this.session.reload()));
  }
}
