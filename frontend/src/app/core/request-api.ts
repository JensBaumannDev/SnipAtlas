import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ContactRequest } from './contact-request';

export interface SentRequest {
  id: number | null;
}

@Service()
export class RequestApi {
  private readonly http = inject(HttpClient);

  send(request: ContactRequest, website: string): Observable<SentRequest> {
    return this.http.post<SentRequest>('/api/requests/', { ...request, website });
  }
}
