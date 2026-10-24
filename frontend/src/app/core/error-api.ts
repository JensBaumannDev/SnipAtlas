import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { ContentIndex, buildIndex } from './content-index';
import { ErrorMessage } from './error-message';

const ERRORS: ErrorMessage[] = [
  // Python
  {
    slug: 'module-not-found-django',
    topic: 'python',
    message: "ModuleNotFoundError: No module named 'django'",
    meaning: 'Python findet das Paket django nicht.',
    cause:
      'Meist ist die virtuelle Umgebung nicht aktiviert, oder django wurde in einer anderen Umgebung installiert.',
    steps: [
      'Virtuelle Umgebung aktivieren, erkennbar an (env) vor der Eingabezeile.',
      'Falls es dann noch fehlt: das Paket in der aktiven Umgebung installieren.',
    ],
    solution: { language: 'terminal', code: 'pip install django' },
  },
  {
    slug: 'python-not-recognized',
    topic: 'python',
    message: "'python' is not recognized as an internal or external command",
    meaning: 'Windows kennt den Befehl python nicht.',
    cause:
      'Python ist nicht installiert, oder bei der Installation wurde „Add Python to PATH“ nicht angehakt.',
    steps: [
      'Statt python den Windows-Starter py ausprobieren.',
      'Oder Python neu installieren und dabei „Add Python to PATH“ anhaken.',
      'Danach das Terminal neu öffnen.',
    ],
    solution: { language: 'terminal', code: 'py --version' },
  },
  {
    slug: 'scripts-disabled',
    topic: 'python',
    message: 'running scripts is disabled on this system',
    meaning:
      'PowerShell blockiert das Ausführen von Skripten, z. B. beim Aktivieren der virtuellen Umgebung oder bei ng.',
    cause: 'Die Ausführungsrichtlinie von Windows erlaubt standardmäßig keine Skripte.',
    steps: [
      'Einmalig für deinen Benutzer lokale Skripte erlauben.',
      'Das Terminal neu öffnen und den Befehl erneut ausführen.',
    ],
    solution: { language: 'terminal', code: 'Set-ExecutionPolicy -Scope CurrentUser RemoteSigned' },
  },

  // Django
  {
    slug: 'no-such-table',
    topic: 'django',
    message: 'django.db.utils.OperationalError: no such table: tasks_task',
    meaning: 'Die Datenbanktabelle für ein Model existiert noch nicht.',
    cause:
      'Nach dem Anlegen oder Ändern eines Models wurden die Migrationen nicht erstellt oder nicht angewendet.',
    steps: [
      'Migrationen erstellen und anwenden.',
      'Prüfen, ob die App in INSTALLED_APPS eingetragen ist.',
    ],
    solution: {
      language: 'terminal',
      code: 'python manage.py makemigrations\npython manage.py migrate',
    },
  },
  {
    slug: 'unapplied-migrations',
    topic: 'django',
    message: 'You have 18 unapplied migration(s).',
    meaning: 'Es gibt Migrationen, die noch nicht auf die Datenbank angewendet wurden.',
    cause: 'Typisch bei einem frischen Projekt oder nach einem git pull.',
    steps: ['Die Migrationen anwenden.'],
    solution: { language: 'terminal', code: 'python manage.py migrate' },
  },
  {
    slug: 'django-port-in-use',
    topic: 'django',
    message: 'Error: That port is already in use.',
    meaning: 'Port 8000 ist schon belegt.',
    cause: 'Ein anderer Entwicklungsserver läuft noch, oft in einem zweiten Terminal-Fenster.',
    steps: ['Den anderen Server mit Strg + C beenden.', 'Oder einen anderen Port verwenden.'],
    solution: { language: 'terminal', code: 'python manage.py runserver 8001' },
  },
  {
    slug: 'secret-key-empty',
    topic: 'django',
    message: 'ImproperlyConfigured: The SECRET_KEY setting must not be empty.',
    meaning: 'Django hat keinen geheimen Schlüssel.',
    cause: 'Der Schlüssel wird aus einer .env-Datei gelesen, die fehlt oder nicht geladen wird.',
    steps: [
      'Im Projektordner eine .env-Datei anlegen und SECRET_KEY eintragen.',
      'Prüfen, ob settings.py die .env-Datei wirklich lädt.',
    ],
    solution: { language: 'env', code: 'SECRET_KEY=hier-ein-langer-zufaelliger-wert' },
  },

  // Django REST Framework
  {
    slug: 'cors-blocked',
    topic: 'django-rest-framework',
    message:
      "Access to fetch at 'http://127.0.0.1:8000/api/tasks/' from origin 'http://localhost:4200' has been blocked by CORS policy",
    meaning: 'Der Browser blockiert die Anfrage vom Frontend an das Backend.',
    cause:
      'Frontend und Backend laufen auf verschiedenen Ports. Das Backend muss solche Anfragen ausdrücklich erlauben.',
    steps: [
      'django-cors-headers installieren und einrichten.',
      'Die Adresse des Frontends in CORS_ALLOWED_ORIGINS eintragen.',
    ],
    solution: { language: 'python', code: "CORS_ALLOWED_ORIGINS = ['http://localhost:4200']" },
  },
  {
    slug: 'credentials-not-provided',
    topic: 'django-rest-framework',
    message: '{"detail": "Authentication credentials were not provided."}',
    meaning: 'Der Endpunkt verlangt einen Login, aber die Anfrage hat keinen mitgeschickt.',
    cause: 'Der Token fehlt im Header der Anfrage oder ist falsch geschrieben.',
    steps: [
      'Den Token im Header Authorization mitschicken, mit dem Wort Token davor.',
      'In Angular am besten über einen Interceptor, dann passiert es bei jeder Anfrage automatisch.',
    ],
  },
  {
    slug: 'csrf-failed',
    topic: 'django-rest-framework',
    message: '{"detail": "CSRF Failed: CSRF token missing."}',
    meaning: 'Django erwartet einen Schutz-Token gegen gefälschte Anfragen.',
    cause:
      'Die API nutzt Login per Sitzung (SessionAuthentication). Dann verlangt Django bei POST, PUT und DELETE einen CSRF-Token.',
    steps: [
      'Für ein getrenntes Frontend Login per Token verwenden.',
      'SessionAuthentication aus DEFAULT_AUTHENTICATION_CLASSES entfernen.',
    ],
  },

  // JavaScript
  {
    slug: 'cannot-read-undefined',
    topic: 'javascript',
    message: "TypeError: Cannot read properties of undefined (reading 'title')",
    meaning: 'Du greifst auf .title von etwas zu, das es (noch) nicht gibt.',
    cause:
      'Meist sind die Daten vom Backend noch nicht geladen, oder der Name der Variable ist falsch.',
    steps: [
      'Mit console.log prüfen, was wirklich in der Variable steht.',
      'Mit ?. absichern, dann gibt es undefined statt eines Fehlers.',
    ],
    solution: { language: 'javascript', code: 'console.log(task?.title);' },
  },
  {
    slug: 'unexpected-token-json',
    topic: 'javascript',
    message: 'SyntaxError: Unexpected token \'<\', "<!DOCTYPE "... is not valid JSON',
    meaning: 'Dein Code erwartet JSON, bekommt aber eine HTML-Seite.',
    cause:
      'Die Adresse stimmt nicht, und der Server liefert eine Fehlerseite (z. B. 404) statt Daten.',
    steps: [
      'Die Adresse direkt im Browser öffnen und ansehen, was zurückkommt.',
      'Auf den Schrägstrich am Ende achten, Django erwartet ihn meist: /api/tasks/',
    ],
  },

  // Angular
  {
    slug: 'no-provider-httpclient',
    topic: 'angular',
    message: 'NullInjectorError: No provider for HttpClient!',
    meaning: 'Angular kann den HttpClient nicht bereitstellen.',
    cause: 'provideHttpClient() fehlt in app.config.ts.',
    steps: ['provideHttpClient() bei providers in app.config.ts eintragen.'],
    solution: { language: 'typescript', code: 'providers: [provideHttpClient()]' },
  },
  {
    slug: 'not-a-known-element',
    topic: 'angular',
    message: "NG8001: 'app-task-list' is not a known element",
    meaning: 'Angular kennt die Komponente im Template nicht.',
    cause: 'Bei Standalone-Komponenten muss jede verwendete Komponente im imports-Array stehen.',
    steps: [
      'Die Komponente bei imports der Komponente eintragen, in deren Template sie verwendet wird.',
      'Den Selektor auf Tippfehler prüfen.',
    ],
    solution: { language: 'typescript', code: 'imports: [TaskListComponent]' },
  },
  {
    slug: 'ng-not-recognized',
    topic: 'angular',
    message: "ng : The term 'ng' is not recognized",
    meaning: 'Das Terminal kennt den Angular-Befehl ng nicht.',
    cause:
      'Die Angular CLI ist nicht global installiert, oder das Terminal wurde danach nicht neu geöffnet.',
    steps: [
      'Die Angular CLI global installieren und das Terminal neu öffnen.',
      'Alternativ npx ng verwenden.',
    ],
    solution: { language: 'terminal', code: 'npm install -g @angular/cli' },
  },
  {
    slug: 'angular-port-in-use',
    topic: 'angular',
    message: 'Port 4200 is already in use.',
    meaning: 'Auf Port 4200 läuft schon etwas, meist ein anderes ng serve.',
    cause: 'Ein zweiter Entwicklungsserver läuft noch.',
    steps: ['Den anderen Server mit Strg + C beenden.', 'Oder einen anderen Port nehmen.'],
    solution: { language: 'terminal', code: 'ng serve --port 4300' },
  },

  // Git
  {
    slug: 'not-a-git-repository',
    topic: 'git',
    message: 'fatal: not a git repository (or any of the parent directories): .git',
    meaning: 'Der aktuelle Ordner ist kein Git-Repository.',
    cause: 'Du bist im falschen Ordner, oder git init wurde noch nicht ausgeführt.',
    steps: [
      'Mit cd in den Projektordner wechseln.',
      'Bei einem neuen Projekt zuerst git init ausführen.',
    ],
    solution: { language: 'terminal', code: 'git init' },
  },
  {
    slug: 'push-rejected',
    topic: 'git',
    message: '! [rejected] main -> main (fetch first)',
    meaning: 'GitHub lehnt deinen Push ab.',
    cause:
      'Auf GitHub gibt es Änderungen, die du lokal noch nicht hast, z. B. eine README, die dort angelegt wurde.',
    steps: ['Erst die Änderungen holen, dann erneut pushen.'],
    solution: { language: 'terminal', code: 'git pull --rebase\ngit push' },
  },
  {
    slug: 'refspec-main',
    topic: 'git',
    message: 'error: src refspec main does not match any',
    meaning: 'Git findet keinen Branch namens main.',
    cause: 'Es gibt noch keinen Commit, oder der Branch heißt master.',
    steps: ['Prüfen, ob es schon einen Commit gibt.', 'Den Branch in main umbenennen.'],
    solution: { language: 'terminal', code: 'git branch -M main' },
  },
  {
    slug: 'permission-denied-publickey',
    topic: 'git',
    message: 'git@github.com: Permission denied (publickey).',
    meaning: 'GitHub erkennt deinen Rechner nicht.',
    cause: 'Für die SSH-Adresse des Repos ist kein SSH-Schlüssel bei GitHub hinterlegt.',
    steps: [
      'Einen SSH-Schlüssel erzeugen und den öffentlichen Teil auf GitHub unter Settings → SSH and GPG keys eintragen.',
      'Oder die HTTPS-Adresse des Repos verwenden.',
    ],
    solution: { language: 'terminal', code: 'ssh-keygen -t ed25519 -C "deine@mail.de"' },
  },
  {
    slug: 'merge-conflict',
    topic: 'git',
    message: 'CONFLICT (content): Merge conflict in src/app/app.component.ts',
    meaning:
      'Zwei Änderungen betreffen dieselben Zeilen, Git kann sie nicht allein zusammenführen.',
    cause: 'Dieselbe Stelle wurde in zwei Branches unterschiedlich geändert.',
    steps: [
      'Die Datei öffnen und die Bereiche zwischen <<<<<<< und >>>>>>> von Hand auflösen.',
      'Danach die Datei vormerken und committen.',
    ],
    solution: { language: 'terminal', code: 'git add .\ngit commit' },
  },

  // Server & Linux
  {
    slug: 'bad-gateway',
    topic: 'server',
    message: '502 Bad Gateway',
    meaning: 'Nginx erreicht die Django-Anwendung dahinter nicht.',
    cause:
      'Gunicorn läuft nicht oder ist abgestürzt, oft wegen eines Fehlers in den Einstellungen.',
    steps: [
      'Den Status von Gunicorn prüfen.',
      'In den Logs nach der eigentlichen Fehlermeldung suchen.',
    ],
    solution: {
      language: 'terminal',
      code: 'sudo systemctl status gunicorn\nsudo journalctl -u gunicorn -n 50',
    },
  },

  // Docker
  {
    slug: 'docker-permission-denied',
    topic: 'docker',
    message: 'permission denied while trying to connect to the Docker daemon socket',
    meaning: 'Dein Benutzer darf Docker nicht steuern.',
    cause: 'Der Benutzer ist nicht in der Gruppe docker.',
    steps: [
      'Den Benutzer zur Gruppe docker hinzufügen.',
      'Ab- und wieder anmelden, damit es wirkt.',
    ],
    solution: { language: 'terminal', code: 'sudo usermod -aG docker $USER' },
  },
];

@Service()
export class ErrorApi {
  getByTopic(topic: string): Observable<ErrorMessage[]> {
    return of(ERRORS.filter((error) => error.topic === topic));
  }

  getSummary(): Observable<{ entries: number; topics: number }> {
    return of({
      entries: ERRORS.length,
      topics: new Set(ERRORS.map((error) => error.topic)).size,
    });
  }

  getIndex(): Observable<ContentIndex> {
    return of(buildIndex(ERRORS));
  }
}
