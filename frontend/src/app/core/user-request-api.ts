import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { UserRequest } from './user-request';

const REQUESTS: UserRequest[] = [
  {
    id: 2,
    kind: 'entry',
    subject: 'git rebase -i erklären',
    date: '2026-10-21',
    status: 'open',
  },
  {
    id: 1,
    kind: 'bug',
    subject: 'Tippfehler bei „Virtuelle Umgebung anlegen“',
    date: '2026-10-12',
    status: 'done',
    answer: 'Danke für den Hinweis, ist korrigiert.',
  },
];

@Service()
export class UserRequestApi {
  getMine(): Observable<UserRequest[]> {
    return of(REQUESTS);
  }
}
