import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable, catchError, of } from 'rxjs';
import { UserRequest } from '../models/user-request';

@Service()
export class UserRequestApi {
  private readonly http = inject(HttpClient);

  getMine(): Observable<UserRequest[]> {
    return this.http.get<UserRequest[]>('/api/me/requests/').pipe(catchError(() => of([])));
  }
}
