import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { Blueprint } from './blueprint';
import { ContentIndex, buildIndex } from './content-index';

const VIRTUAL_ENV = {
  win: 'python -m venv env\nenv\\Scripts\\activate',
  unix: 'python3 -m venv env\nsource env/bin/activate',
};

const BLUEPRINTS: Blueprint[] = [
  // New Django project
  {
    slug: 'django-projekt-anlegen',
    topic: 'django',
    title: 'Neues Django-Projekt anlegen',
    summary:
      'Vom leeren Ordner bis zum ersten Model in der Datenbank, mit sauberem Start auf GitHub.',
    steps: [
      {
        slug: 'ordner-anlegen',
        title: 'Projektordner anlegen',
        why: 'Alles, was zum Projekt gehört, liegt in einem Ordner. Diesen Ordner öffnest du später in VS Code.',
        code: [{ language: 'terminal', code: 'mkdir {{project}}\ncd {{project}}' }],
      },
      {
        slug: 'virtuelle-umgebung',
        title: 'Virtuelle Umgebung einrichten',
        why: 'Jedes Projekt bekommt seine eigenen Pakete in eigenen Versionen. So stören sich zwei Projekte auf deinem Rechner nicht gegenseitig.',
        code: [{ language: 'terminal', code: VIRTUAL_ENV }],
        note: 'Danach steht (env) vor der Eingabezeile. Fehlt es, ist die Umgebung nicht aktiv und pip installiert die Pakete für den ganzen Rechner.',
      },
      {
        slug: 'django-installieren',
        title: 'Django installieren',
        why: 'pip installiert Django in die aktive Umgebung. Die Datei requirements.txt hält fest, welche Pakete das Projekt in welcher Version braucht, damit andere es genauso einrichten können.',
        code: [{ language: 'terminal', code: 'pip install django\npip freeze > requirements.txt' }],
        note: 'pip freeze ohne > zeigt dir nur an, was gerade installiert ist.',
      },
      {
        slug: 'projekt-erstellen',
        title: 'Django-Projekt erstellen',
        why: 'Legt manage.py und den Ordner core mit settings.py und urls.py an. Über manage.py steuerst du ab jetzt das Projekt.',
        code: [{ language: 'terminal', code: 'django-admin startproject core .' }],
        note: 'Der Punkt am Ende legt das Projekt im aktuellen Ordner an. Ohne ihn bekommst du einen zusätzlichen Unterordner.',
      },
      {
        slug: 'gitignore-und-erster-commit',
        title: '.gitignore anlegen und erster Commit',
        why: 'Die .gitignore legt fest, was nicht ins Repository gehört: die virtuelle Umgebung, Cache-Dateien, die lokale Datenbank und Geheimnisse wie die .env.',
        code: [
          { language: 'gitignore', code: 'env/\n__pycache__/\n*.pyc\ndb.sqlite3\n.env' },
          {
            language: 'terminal',
            code: 'git init\ngit add .\ngit commit -m "chore: initial django setup"',
          },
        ],
        note: 'Erst committen, wenn die .gitignore da ist. Was einmal auf GitHub liegt, bleibt in der Historie, auch wenn du es später löschst.',
      },
      {
        slug: 'app-erstellen',
        title: 'Django-App erstellen',
        why: 'Eine App bündelt einen Bereich deines Projekts, zum Beispiel Aufgaben oder Benutzer, mit eigenen Models, Views und URLs.',
        code: [{ language: 'terminal', code: 'python manage.py startapp tasks' }],
        note: 'Überleg vorher, welche Bereiche dein Projekt hat. Für ein kleines Projekt reicht oft eine App.',
      },
      {
        slug: 'app-registrieren',
        title: 'App in settings.py eintragen',
        why: 'Erst wenn die App in INSTALLED_APPS steht, findet Django ihre Models und Migrationen.',
        code: [
          {
            language: 'python',
            code: "# core/settings.py\nINSTALLED_APPS = [\n    # ...\n    'tasks',\n]",
          },
        ],
      },
      {
        slug: 'model-und-migration',
        title: 'Model schreiben und migrieren',
        why: 'Das Model beschreibt eine Tabelle. makemigrations schreibt die Änderung als Datei, migrate legt die Tabelle in der Datenbank an.',
        code: [
          {
            language: 'python',
            code: '# tasks/models.py\nfrom django.db import models\n\n\nclass Task(models.Model):\n    title = models.CharField(max_length=200)\n    done = models.BooleanField(default=False)',
          },
          {
            language: 'terminal',
            code: 'python manage.py makemigrations\npython manage.py migrate',
          },
        ],
        note: 'Nach jeder Änderung an models.py brauchst du beide Befehle noch einmal.',
      },
      {
        slug: 'server-starten',
        title: 'Entwicklungsserver starten',
        why: 'Der Server zeigt dein Projekt unter http://127.0.0.1:8000 im Browser. Siehst du die Startseite von Django, läuft alles.',
        code: [{ language: 'terminal', code: 'python manage.py runserver' }],
        note: 'Strg + C beendet den Server.',
      },
      {
        slug: 'regelmaessig-committen',
        title: 'Regelmäßig committen',
        why: 'Kleine Commits zeigen, wie dein Projekt gewachsen ist, und lassen sich leichter rückgängig machen als ein großer.',
        code: [
          {
            language: 'terminal',
            code: 'pip freeze > requirements.txt\ngit add .\ngit commit -m "feat: add task model"\ngit push',
          },
        ],
        note: 'Neues Paket installiert? Dann requirements.txt neu schreiben, bevor du committest.',
      },
    ],
  },

  // Existing Django project
  {
    slug: 'django-projekt-klonen',
    topic: 'django',
    title: 'Bestehendes Django-Projekt einrichten',
    summary: 'Ein Django-Projekt von GitHub holen und auf dem eigenen Rechner zum Laufen bringen.',
    steps: [
      {
        slug: 'repo-klonen',
        title: 'Repository klonen',
        why: 'Holt das Projekt mit seiner ganzen Historie auf deinen Rechner.',
        code: [
          {
            language: 'terminal',
            code: 'git clone https://github.com/{{githubUser}}/{{repo}}.git\ncd {{repo}}',
          },
        ],
      },
      {
        slug: 'virtuelle-umgebung',
        title: 'Virtuelle Umgebung einrichten',
        why: 'Die Umgebung liegt nicht im Repository. Jeder legt sie auf seinem Rechner selbst an.',
        code: [{ language: 'terminal', code: VIRTUAL_ENV }],
        note: 'Danach steht (env) vor der Eingabezeile.',
      },
      {
        slug: 'pakete-installieren',
        title: 'Pakete installieren',
        why: 'requirements.txt enthält alle Pakete in genau den Versionen, mit denen das Projekt gebaut wurde.',
        code: [{ language: 'terminal', code: 'pip install -r requirements.txt\npip freeze' }],
        note: 'pip freeze sollte danach dieselben Pakete zeigen, die in requirements.txt stehen.',
      },
      {
        slug: 'migrieren',
        title: 'Migrationen ausführen',
        why: 'Legt die Tabellen in deiner lokalen Datenbank an. Die Migrationsdateien liegen schon im Repository.',
        code: [{ language: 'terminal', code: 'python manage.py migrate' }],
        note: 'makemigrations brauchst du hier nicht. Das ist nur nötig, wenn du selbst Models änderst.',
      },
      {
        slug: 'server-starten',
        title: 'Entwicklungsserver starten',
        why: 'Läuft der Server ohne Fehler, ist das Projekt fertig eingerichtet.',
        code: [{ language: 'terminal', code: 'python manage.py runserver' }],
        note: 'Startet er nicht, fehlt oft die .env. Liegt eine .env.template im Projekt, kopiere sie nach .env und trag deine Werte ein.',
      },
    ],
  },

  // Secret key in .env
  {
    slug: 'secret-key-in-env',
    topic: 'django',
    title: 'SECRET_KEY in eine .env auslagern',
    summary: 'Den geheimen Schlüssel aus settings.py holen, damit er nie auf GitHub landet.',
    steps: [
      {
        slug: 'env-anlegen',
        title: '.env im Projektordner anlegen',
        why: 'Der SECRET_KEY sichert unter anderem Sitzungen und Links zum Zurücksetzen von Passwörtern. Er gehört nicht in den Code. Die .env liegt neben manage.py.',
        code: [
          {
            language: 'terminal',
            code: 'python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"',
          },
          { language: 'env', code: 'SECRET_KEY=hier-den-erzeugten-schluessel-einsetzen' },
        ],
        note: 'Stand der Schlüssel schon einmal auf GitHub, nimm einen neuen. Der erste Befehl erzeugt dir einen.',
      },
      {
        slug: 'env-ignorieren',
        title: '.env in die .gitignore eintragen',
        why: 'So kann Git die Datei nie mit committen, auch nicht aus Versehen mit git add .',
        code: [{ language: 'gitignore', code: '.env' }],
      },
      {
        slug: 'dotenv-installieren',
        title: 'python-dotenv installieren',
        why: 'Das Paket liest die .env beim Start und stellt ihre Werte als Umgebungsvariablen bereit.',
        code: [
          {
            language: 'terminal',
            code: 'pip install python-dotenv\npip freeze > requirements.txt',
          },
        ],
      },
      {
        slug: 'settings-anpassen',
        title: 'Schlüssel in settings.py laden',
        why: 'settings.py holt den Schlüssel jetzt aus der Umgebung statt aus dem Code. Fehlt er, startet Django gar nicht erst.',
        code: [
          {
            language: 'python',
            code: "# core/settings.py\nimport os\nfrom pathlib import Path\n\nfrom dotenv import load_dotenv\n\nBASE_DIR = Path(__file__).resolve().parent.parent\nload_dotenv(BASE_DIR / '.env')\n\nSECRET_KEY = os.getenv('SECRET_KEY')\nif not SECRET_KEY:\n    raise RuntimeError('SECRET_KEY fehlt in der .env')",
          },
        ],
        note: 'Die alte Zeile SECRET_KEY = "django-insecure-…" löschst du.',
      },
      {
        slug: 'vorlage-anlegen',
        title: '.env.template für das Repository anlegen',
        why: 'Die Vorlage darf ins Repository. Sie zeigt allen, die das Projekt klonen, welche Werte sie brauchen, ohne die echten zu verraten.',
        code: [{ language: 'env', code: 'SECRET_KEY=hier-deinen-schluessel-eintragen' }],
      },
      {
        slug: 'env-aus-vorlage',
        title: 'Nach dem Klonen: .env aus der Vorlage erstellen',
        why: 'In einem frisch geklonten Projekt fehlt die .env. Kopiere die Vorlage und trag deinen eigenen Schlüssel ein.',
        code: [
          {
            language: 'terminal',
            code: { win: 'copy .env.template .env', unix: 'cp .env.template .env' },
          },
        ],
      },
    ],
  },
];

@Service()
export class BlueprintApi {
  getAll(): Observable<Blueprint[]> {
    return of(BLUEPRINTS);
  }

  getBySlug(slug: string): Observable<Blueprint | undefined> {
    return of(BLUEPRINTS.find((blueprint) => blueprint.slug === slug));
  }

  getSummary(): Observable<{ blueprints: number; steps: number }> {
    return of({
      blueprints: BLUEPRINTS.length,
      steps: BLUEPRINTS.reduce((sum, blueprint) => sum + blueprint.steps.length, 0),
    });
  }

  getIndex(): Observable<ContentIndex> {
    return of(buildIndex(BLUEPRINTS));
  }
}
