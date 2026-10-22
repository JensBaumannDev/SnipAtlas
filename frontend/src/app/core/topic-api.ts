import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { Group } from './topic';

const GROUPS: Group[] = [
  {
    slug: 'frontend',
    name: 'Frontend',
    topics: [
      {
        slug: 'html',
        name: 'HTML',
        color: '#e34f26',
        subtopics: [
          { slug: 'grundgeruest', name: 'Grundgerüst' },
          { slug: 'elemente', name: 'Elemente' },
          { slug: 'formulare', name: 'Formulare' },
          { slug: 'barrierefreiheit', name: 'Barrierefreiheit' },
          { slug: 'seo', name: 'SEO & Meta-Tags' },
        ],
      },
      {
        slug: 'css',
        name: 'CSS',
        color: '#1572b6',
        subtopics: [
          { slug: 'selektoren', name: 'Selektoren' },
          { slug: 'box-modell', name: 'Box-Modell' },
          { slug: 'flexbox', name: 'Flexbox' },
          { slug: 'grid', name: 'Grid' },
          { slug: 'responsive', name: 'Responsive' },
          { slug: 'variablen', name: 'Variablen' },
          { slug: 'scss', name: 'SCSS' },
        ],
      },
      {
        slug: 'javascript',
        name: 'JavaScript',
        color: '#d9a400',
        subtopics: [
          { slug: 'variablen-datentypen', name: 'Variablen & Datentypen' },
          { slug: 'schleifen', name: 'Schleifen' },
          { slug: 'arrays', name: 'Arrays' },
          { slug: 'strings', name: 'Strings' },
          { slug: 'objekte', name: 'Objekte' },
          { slug: 'funktionen', name: 'Funktionen' },
          { slug: 'dom-events', name: 'DOM & Events' },
          { slug: 'async', name: 'Async & Promises' },
          { slug: 'daten-laden', name: 'Daten laden' },
          { slug: 'fehlerbehandlung', name: 'Fehlerbehandlung' },
        ],
      },
      {
        slug: 'typescript',
        name: 'TypeScript',
        color: '#3178c6',
        subtopics: [
          { slug: 'typen', name: 'Typen' },
          { slug: 'interfaces', name: 'Interfaces' },
          { slug: 'funktionen', name: 'Funktionen' },
          { slug: 'generics', name: 'Generics' },
          { slug: 'tsconfig', name: 'tsconfig' },
        ],
      },
      {
        slug: 'angular',
        name: 'Angular',
        color: '#dd0031',
        subtopics: [
          { slug: 'cli', name: 'Projekt & CLI' },
          { slug: 'komponenten', name: 'Komponenten' },
          { slug: 'templates', name: 'Templates' },
          { slug: 'signals', name: 'Signals' },
          { slug: 'routing', name: 'Routing' },
          { slug: 'formulare', name: 'Formulare' },
          { slug: 'services-http', name: 'Services & HTTP' },
          { slug: 'interceptor', name: 'Interceptor' },
          { slug: 'rxjs', name: 'RxJS' },
          { slug: 'tests', name: 'Tests' },
          { slug: 'build', name: 'Build & Deployment' },
          { slug: 'updates', name: 'Updates' },
        ],
      },
    ],
  },
  {
    slug: 'backend',
    name: 'Backend',
    topics: [
      {
        slug: 'python',
        name: 'Python',
        color: '#3776ab',
        subtopics: [
          { slug: 'umgebung-pakete', name: 'Umgebung & Pakete' },
          { slug: 'variablen-datentypen', name: 'Variablen & Datentypen' },
          { slug: 'schleifen', name: 'Schleifen' },
          { slug: 'listen', name: 'Listen' },
          { slug: 'dictionaries', name: 'Dictionaries' },
          { slug: 'strings', name: 'Strings' },
          { slug: 'funktionen', name: 'Funktionen' },
          { slug: 'klassen', name: 'Klassen' },
          { slug: 'dateien', name: 'Dateien' },
          { slug: 'fehlerbehandlung', name: 'Fehlerbehandlung' },
        ],
      },
      {
        slug: 'django',
        name: 'Django',
        color: '#2ba36b',
        subtopics: [
          { slug: 'projekt', name: 'Projekt einrichten' },
          { slug: 'models-migrationen', name: 'Models & Migrationen' },
          { slug: 'admin', name: 'Admin' },
          { slug: 'urls-views', name: 'URLs & Views' },
          { slug: 'einstellungen', name: 'Einstellungen & .env' },
          { slug: 'statische-dateien', name: 'Statische Dateien' },
          { slug: 'e-mail', name: 'E-Mail' },
          { slug: 'tests', name: 'Tests' },
          { slug: 'deployment', name: 'Deployment' },
        ],
      },
      {
        slug: 'django-rest-framework',
        name: 'Django REST Framework',
        color: '#c9573a',
        subtopics: [
          { slug: 'einrichtung', name: 'Einrichtung' },
          { slug: 'serializer', name: 'Serializer' },
          { slug: 'views-viewsets', name: 'Views & ViewSets' },
          { slug: 'router-urls', name: 'Router & URLs' },
          { slug: 'authentifizierung', name: 'Authentifizierung' },
          { slug: 'berechtigungen', name: 'Berechtigungen' },
          { slug: 'pagination-filter', name: 'Pagination & Filter' },
          { slug: 'cors', name: 'CORS' },
          { slug: 'tests', name: 'Tests' },
        ],
      },
      {
        slug: 'postgresql',
        name: 'PostgreSQL',
        color: '#4169e1',
        subtopics: [
          { slug: 'installation', name: 'Installation' },
          { slug: 'psql', name: 'psql' },
          { slug: 'datenbank-benutzer', name: 'Datenbank & Benutzer' },
          { slug: 'django-verbinden', name: 'Mit Django verbinden' },
          { slug: 'backup', name: 'Backup & Restore' },
        ],
      },
    ],
  },
  {
    slug: 'tools',
    name: 'Tools',
    topics: [
      {
        slug: 'terminal',
        name: 'Terminal',
        color: '#5b6b7f',
        subtopics: [
          { slug: 'navigieren', name: 'Navigieren' },
          { slug: 'dateien-ordner', name: 'Dateien & Ordner' },
          { slug: 'umgebungsvariablen', name: 'Umgebungsvariablen' },
          { slug: 'prozesse-ports', name: 'Prozesse & Ports' },
          { slug: 'tastenkuerzel', name: 'Tastenkürzel' },
        ],
      },
      {
        slug: 'git',
        name: 'Git & GitHub',
        color: '#f05032',
        subtopics: [
          { slug: 'einrichten', name: 'Einrichten' },
          { slug: 'alltag', name: 'Alltag' },
          { slug: 'branches', name: 'Branches' },
          { slug: 'merge-konflikte', name: 'Merge & Konflikte' },
          { slug: 'pull-requests', name: 'Pull Requests' },
          { slug: 'stash', name: 'Stash' },
          { slug: 'rueckgaengig', name: 'Rückgängig machen' },
          { slug: 'gitignore', name: '.gitignore' },
          { slug: 'ssh-schluessel', name: 'SSH-Schlüssel' },
        ],
      },
      {
        slug: 'npm',
        name: 'Node & npm',
        color: '#cb3837',
        subtopics: [
          { slug: 'node-versionen', name: 'Node-Versionen' },
          { slug: 'pakete', name: 'Pakete' },
          { slug: 'skripte', name: 'Skripte' },
          { slug: 'package-json', name: 'package.json' },
          { slug: 'fehlersuche', name: 'Fehlersuche' },
        ],
      },
      {
        slug: 'docker',
        name: 'Docker',
        color: '#1d9bd7',
        subtopics: [
          { slug: 'container', name: 'Container steuern' },
          { slug: 'images-dockerfile', name: 'Images & Dockerfile' },
          { slug: 'compose', name: 'Compose' },
          { slug: 'volumes', name: 'Volumes' },
          { slug: 'umgebungsvariablen', name: 'Umgebungsvariablen' },
          { slug: 'fehlersuche', name: 'Fehlersuche' },
          { slug: 'aufraeumen', name: 'Aufräumen' },
        ],
      },
      {
        slug: 'server',
        name: 'Server & Linux',
        color: '#5b6b7f',
        subtopics: [
          { slug: 'verbindung', name: 'Verbindung' },
          { slug: 'benutzer-rechte', name: 'Benutzer & Rechte' },
          { slug: 'dateien-uebertragen', name: 'Dateien übertragen' },
          { slug: 'pakete', name: 'Pakete' },
          { slug: 'dienste-logs', name: 'Dienste & Logs' },
          { slug: 'firewall', name: 'Firewall' },
          { slug: 'nginx', name: 'Nginx' },
          { slug: 'https', name: 'HTTPS' },
          { slug: 'domain-dns', name: 'Domain & DNS' },
        ],
      },
    ],
  },
];

@Service()
export class TopicApi {
  getGroups(): Observable<Group[]> {
    return of(GROUPS);
  }
}
