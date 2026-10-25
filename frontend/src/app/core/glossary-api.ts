import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { GlossaryTerm } from './glossary-term';

const TERMS: GlossaryTerm[] = [
  {
    slug: 'api',
    term: 'API',
    aliases: ['Schnittstelle'],
    definition:
      'Schnittstelle, über die Programme miteinander reden. Dein Angular-Frontend fragt über die API Daten beim Django-Backend an.',
  },
  {
    slug: 'authentifizierung',
    term: 'Authentifizierung',
    aliases: [],
    definition:
      'Prüfen, wer jemand ist, zum Beispiel per Login. Nicht verwechseln mit Autorisierung: Was darf diese Person?',
  },
  {
    slug: 'backend',
    term: 'Backend',
    aliases: [],
    definition:
      'Der Teil einer Anwendung, der auf dem Server läuft: Datenbank, Logik und API. Bei dir: Django.',
  },
  {
    slug: 'branch',
    term: 'Branch',
    aliases: ['Branches'],
    definition:
      'Ein eigener Entwicklungszweig in Git. Dort arbeitest du an einem Feature, ohne main zu verändern.',
  },
  {
    slug: 'cli',
    term: 'CLI',
    aliases: ['Kommandozeile'],
    definition:
      'Command Line Interface: ein Programm, das man im Terminal mit Befehlen steuert, z. B. ng oder git.',
  },
  {
    slug: 'commit',
    term: 'Commit',
    aliases: ['Commits', 'committet', 'committen'],
    definition: 'Ein gespeicherter Zwischenstand in Git, mit einer Nachricht, was sich geändert hat.',
  },
  {
    slug: 'container',
    term: 'Container',
    aliases: ['Containern'],
    definition:
      'Ein abgeschlossenes Paket aus Anwendung und allem, was sie zum Laufen braucht. Läuft überall gleich.',
  },
  {
    slug: 'cors',
    term: 'CORS',
    aliases: [],
    definition:
      'Sicherheitsregel im Browser: Eine Seite darf nur Daten von einer anderen Adresse laden, wenn diese es ausdrücklich erlaubt.',
  },
  {
    slug: 'csrf',
    term: 'CSRF',
    aliases: [],
    definition:
      'Angriff, bei dem eine fremde Seite im Namen eines angemeldeten Benutzers Anfragen abschickt. Django schützt sich mit einem CSRF-Token.',
  },
  {
    slug: 'docker-compose',
    term: 'Docker Compose',
    aliases: [],
    definition:
      'Startet mehrere Container gemeinsam, z. B. Backend, Datenbank und Frontend. Beschrieben in einer docker-compose.yml.',
  },
  {
    slug: 'domain',
    term: 'Domain',
    aliases: [],
    definition:
      'Der Name einer Website, z. B. snipatlas.com. Über DNS zeigt er auf die IP-Adresse deines Servers.',
  },
  {
    slug: 'endpunkt',
    term: 'Endpunkt',
    aliases: ['Endpunkte', 'Endpoint'],
    definition:
      'Eine bestimmte Adresse einer API, z. B. /api/tasks/. Jeder Endpunkt liefert oder ändert bestimmte Daten.',
  },
  {
    slug: 'firewall',
    term: 'Firewall',
    aliases: [],
    definition: 'Regelt, welche Verbindungen auf einem Server erlaubt sind.',
  },
  {
    slug: 'frontend',
    term: 'Frontend',
    aliases: [],
    definition:
      'Der Teil einer Anwendung, den Benutzer im Browser sehen und bedienen. Bei dir: Angular.',
  },
  {
    slug: 'gunicorn',
    term: 'Gunicorn',
    aliases: [],
    definition:
      'Programm, das eine Django-Anwendung auf dem Server ausführt. Nginx leitet die Anfragen aus dem Internet an Gunicorn weiter.',
  },
  {
    slug: 'http-methoden',
    term: 'HTTP-Methoden',
    aliases: ['HTTP-Methode'],
    definition:
      'Die Art einer Anfrage: GET liest Daten, POST legt an, PUT und PATCH ändern, DELETE löscht.',
  },
  {
    slug: 'https',
    term: 'HTTPS',
    aliases: ['SSL', 'Zertifikat'],
    definition:
      'Verschlüsselte Verbindung zwischen Browser und Server. Braucht ein Zertifikat, z. B. kostenlos von Let’s Encrypt.',
  },
  {
    slug: 'interface',
    term: 'Interface',
    aliases: ['Interfaces'],
    definition:
      'In TypeScript eine Beschreibung, welche Felder ein Objekt hat. Fehler fallen dadurch schon beim Schreiben auf.',
  },
  {
    slug: 'json',
    term: 'JSON',
    aliases: [],
    definition:
      'Textformat für Daten, z. B. {"title": "Code"}. So tauschen Frontend und Backend Daten aus.',
  },
  {
    slug: 'komponente',
    term: 'Komponente',
    aliases: ['Komponenten'],
    definition:
      'Ein Baustein der Oberfläche in Angular, bestehend aus Template, Styles und einer TypeScript-Klasse.',
  },
  {
    slug: 'localhost',
    term: 'localhost',
    aliases: ['127.0.0.1'],
    definition: 'Dein eigener Rechner als Server. 127.0.0.1 ist dieselbe Adresse.',
  },
  {
    slug: 'merge',
    term: 'Merge',
    aliases: ['Merge-Konflikt'],
    definition:
      'Zwei Branches zusammenführen. Ändern beide dieselben Zeilen, entsteht ein Merge-Konflikt.',
  },
  {
    slug: 'middleware',
    term: 'Middleware',
    aliases: [],
    definition:
      'Code, der in Django bei jeder Anfrage zwischen Server und deiner View läuft, z. B. für CORS oder Sitzungen.',
  },
  {
    slug: 'migration',
    term: 'Migration',
    aliases: ['Migrationen'],
    definition:
      'Eine Datei, die beschreibt, wie sich die Datenbank ändern soll. Django erzeugt sie aus deinen Models.',
  },
  {
    slug: 'model',
    term: 'Model',
    aliases: ['Models'],
    definition: 'Eine Python-Klasse in Django, die eine Datenbanktabelle beschreibt.',
  },
  {
    slug: 'nginx',
    term: 'Nginx',
    aliases: [],
    definition:
      'Webserver, der Anfragen aus dem Internet annimmt, statische Dateien ausliefert und den Rest an Gunicorn weitergibt.',
  },
  {
    slug: 'observable',
    term: 'Observable',
    aliases: ['Observables'],
    definition:
      'In Angular ein Datenstrom, der später Werte liefert, z. B. die Antwort des HttpClient. Mit subscribe() hört man darauf.',
  },
  {
    slug: 'orm',
    term: 'ORM',
    aliases: [],
    definition:
      'Übersetzt zwischen Python-Objekten und der Datenbank. Du schreibst Task.objects.all() statt SQL.',
  },
  {
    slug: 'paket',
    term: 'Paket',
    aliases: ['Pakete'],
    definition:
      'Fertiger Code anderer Entwickler, den du installierst: mit pip in Python, mit npm in JavaScript.',
  },
  {
    slug: 'port',
    term: 'Port',
    aliases: ['Ports'],
    definition:
      'Eine Nummer, unter der ein Programm auf dem Rechner erreichbar ist, z. B. 8000 für Django oder 4200 für Angular.',
  },
  {
    slug: 'pull-request',
    term: 'Pull Request',
    aliases: ['Pull Requests'],
    definition:
      'Anfrage auf GitHub, die Änderungen aus einem Branch in main zu übernehmen. Vorher kann man sie prüfen und kommentieren.',
  },
  {
    slug: 'repository',
    term: 'Repository',
    aliases: ['Repo', 'Repos'],
    definition: 'Ein Projekt unter Git-Verwaltung, lokal oder auf GitHub. Kurz: Repo.',
  },
  {
    slug: 'rest',
    term: 'REST',
    aliases: ['REST-API'],
    definition:
      'Ein Stil für APIs: Daten sind über Adressen erreichbar und werden mit HTTP-Methoden gelesen und geändert.',
  },
  {
    slug: 'router',
    term: 'Router',
    aliases: [],
    definition:
      'In Django REST erzeugt er automatisch die Adressen für ein ViewSet. In Angular steuert er, welche Seite bei welcher Adresse erscheint.',
  },
  {
    slug: 'serializer',
    term: 'Serializer',
    aliases: [],
    definition: 'Wandelt in Django REST Model-Objekte in JSON um und prüft eingehende Daten.',
  },
  {
    slug: 'service',
    term: 'Service',
    aliases: ['Services'],
    definition:
      'In Angular eine Klasse für Logik und Datenzugriff, die mehrere Komponenten gemeinsam nutzen.',
  },
  {
    slug: 'ssh',
    term: 'SSH',
    aliases: [],
    definition: 'Verschlüsselte Verbindung zu einem anderen Rechner, um dort im Terminal zu arbeiten.',
  },
  {
    slug: 'statuscode',
    term: 'Statuscode',
    aliases: ['Statuscodes'],
    definition:
      'Zahl in der Antwort des Servers: 200 OK, 201 angelegt, 400 fehlerhafte Anfrage, 401 nicht angemeldet, 404 nicht gefunden, 500 Serverfehler.',
  },
  {
    slug: 'template',
    term: 'Template',
    aliases: ['Templates'],
    definition:
      'Die HTML-Vorlage einer Angular-Komponente, mit Platzhaltern wie {{ task.title }}.',
  },
  {
    slug: 'token',
    term: 'Token',
    aliases: [],
    definition:
      'Ein langer geheimer Schlüssel, mit dem sich das Frontend bei jeder Anfrage als angemeldeter Benutzer ausweist.',
  },
  {
    slug: 'umgebungsvariable',
    term: 'Umgebungsvariable',
    aliases: ['Umgebungsvariablen'],
    definition:
      'Ein Wert, der außerhalb des Codes gesetzt wird, z. B. in einer .env-Datei. So landen Passwörter nicht im Repo.',
  },
  {
    slug: 'viewset',
    term: 'ViewSet',
    aliases: ['ViewSets'],
    definition:
      'Bündelt in Django REST alle Aktionen für ein Model: auflisten, anzeigen, anlegen, ändern, löschen.',
  },
  {
    slug: 'virtuelle-umgebung',
    term: 'Virtuelle Umgebung',
    aliases: ['venv'],
    definition:
      'Ein eigener Ordner mit Python-Paketen nur für ein Projekt, damit sich Projekte nicht in die Quere kommen.',
  },
];

@Service()
export class GlossaryApi {
  getAll(): Observable<GlossaryTerm[]> {
    return of(TERMS);
  }
}
