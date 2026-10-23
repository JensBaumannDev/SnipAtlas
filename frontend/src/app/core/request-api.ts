import { Service } from '@angular/core';
import { Observable, delay, of } from 'rxjs';
import { ContactRequest } from './contact-request';

const SIMULATED_DELAY = 600;

@Service()
export class RequestApi {
  send(request: ContactRequest): Observable<ContactRequest> {
    return of(request).pipe(delay(SIMULATED_DELAY));
  }
}
