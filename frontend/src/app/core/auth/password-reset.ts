import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface ResetConfirmation {
  uid: string;
  token: string;
  password: string;
}

const URL = '/api/auth/password-reset/';

@Service()
export class PasswordReset {
  private readonly http = inject(HttpClient);

  request(email: string): Observable<void> {
    return this.http.post<void>(URL, { email });
  }

  confirm(confirmation: ResetConfirmation): Observable<void> {
    return this.http.post<void>(`${URL}confirm/`, confirmation);
  }
}
