import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { NewsItem } from './news';

const NEWS: NewsItem[] = [
  {
    date: '2026-10-20',
    title: 'Docker: Container steuern und Fehler finden',
    link: ['/befehle', 'docker', 'fehlersuche'],
  },
  {
    date: '2026-10-14',
    title: 'Git: Branches anlegen und Änderungen rückgängig machen',
    link: ['/befehle', 'git', 'branches'],
  },
  {
    date: '2026-10-08',
    title: 'Django REST Framework: Login per Token einrichten',
    link: ['/konzepte', 'django-rest-framework', 'authentifizierung'],
  },
  {
    date: '2026-10-01',
    title: 'Python: Umgebung und Pakete mit venv und pip',
    link: ['/befehle', 'python', 'umgebung-pakete'],
  },
];

@Service()
export class NewsApi {
  getLatest(): Observable<NewsItem[]> {
    return of(NEWS);
  }
}
