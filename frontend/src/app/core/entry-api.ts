import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { Entry } from './entry';

const ENTRIES: Entry[] = [
  // Git
  {
    slug: 'projekt-mit-github-verbinden',
    topic: 'git',
    subtopic: 'einrichten',
    title: 'Neues Projekt mit GitHub verbinden',
    description:
      'Einmal am Anfang: Ordner zum Git-Repo machen und mit einem leeren GitHub-Repo verknüpfen.',
    language: 'terminal',
    code: 'git init\ngit add .\ngit commit -m "Erster Commit"\ngit branch -M main\ngit remote add origin https://github.com/NAME/REPO.git\ngit push -u origin main',
  },
  {
    slug: 'repo-herunterladen',
    topic: 'git',
    subtopic: 'einrichten',
    title: 'Repo herunterladen',
    description: 'Ein bestehendes Projekt von GitHub auf den Rechner holen.',
    language: 'terminal',
    code: 'git clone https://github.com/NAME/REPO.git',
  },
  {
    slug: 'speichern-und-hochladen',
    topic: 'git',
    subtopic: 'alltag',
    title: 'Täglicher Ablauf: speichern und hochladen',
    description: 'Änderungen vormerken, mit Nachricht speichern und zu GitHub schicken.',
    language: 'terminal',
    code: 'git status\ngit add .\ngit commit -m "Was ich geändert habe"\ngit push',
  },
  {
    slug: 'neueste-aenderungen-holen',
    topic: 'git',
    subtopic: 'alltag',
    title: 'Neueste Änderungen holen',
    description: 'Bevor du anfängst zu arbeiten, besonders wenn mehrere am Repo arbeiten.',
    language: 'terminal',
    code: 'git pull',
  },
  {
    slug: 'verlauf-anzeigen',
    topic: 'git',
    subtopic: 'alltag',
    title: 'Verlauf kompakt anzeigen',
    description: 'Wer hat wann was committet, als Baum.',
    language: 'terminal',
    code: 'git log --oneline --graph --all',
  },
  {
    slug: 'branch-anlegen-und-wechseln',
    topic: 'git',
    subtopic: 'branches',
    title: 'Neuen Branch anlegen und wechseln',
    description: 'Für ein neues Feature, ohne main zu verändern.',
    language: 'terminal',
    code: 'git switch -c feature/login\n\n# zurück zu main\ngit switch main',
  },
  {
    slug: 'commit-nachricht-aendern',
    topic: 'git',
    subtopic: 'rueckgaengig',
    title: 'Letzte Commit-Nachricht ändern',
    description: 'Nur solange der Commit noch nicht gepusht ist.',
    language: 'terminal',
    code: 'git commit --amend -m "Neue Nachricht"',
  },
  {
    slug: 'datei-aus-staging-nehmen',
    topic: 'git',
    subtopic: 'rueckgaengig',
    title: 'Datei wieder aus „git add“ herausnehmen',
    description: 'Die Änderung bleibt erhalten, wird nur nicht mit committet.',
    language: 'terminal',
    code: 'git restore --staged datei.py',
  },

  // Python
  {
    slug: 'virtuelle-umgebung',
    topic: 'python',
    subtopic: 'umgebung-pakete',
    title: 'Virtuelle Umgebung anlegen und aktivieren',
    description:
      'Jedes Projekt bekommt seine eigenen Pakete. Danach steht (env) vor der Eingabezeile.',
    language: 'terminal',
    code: {
      win: 'python -m venv env\nenv\\Scripts\\activate',
      unix: 'python3 -m venv env\nsource env/bin/activate',
    },
  },
  {
    slug: 'requirements-txt',
    topic: 'python',
    subtopic: 'umgebung-pakete',
    title: 'Pakete festhalten und wieder installieren',
    description: 'requirements.txt gehört ins Repo, der env-Ordner nicht.',
    language: 'terminal',
    code: 'pip freeze > requirements.txt\n\n# auf einem anderen Rechner\npip install -r requirements.txt',
  },

  // Django
  {
    slug: 'django-projekt-anlegen',
    topic: 'django',
    subtopic: 'projekt',
    title: 'Django installieren und Projekt anlegen',
    description:
      'Der Punkt am Ende legt das Projekt im aktuellen Ordner an, ohne zusätzlichen Unterordner.',
    language: 'terminal',
    code: 'pip install django\ndjango-admin startproject core .',
  },
  {
    slug: 'neue-app-anlegen',
    topic: 'django',
    subtopic: 'projekt',
    title: 'Neue App anlegen',
    description: 'Danach den App-Namen in settings.py bei INSTALLED_APPS eintragen.',
    language: 'terminal',
    code: 'python manage.py startapp tasks',
  },
  {
    slug: 'entwicklungsserver-starten',
    topic: 'django',
    subtopic: 'projekt',
    title: 'Entwicklungsserver starten',
    description: 'Läuft dann unter http://127.0.0.1:8000',
    language: 'terminal',
    code: 'python manage.py runserver',
  },
  {
    slug: 'migrationen',
    topic: 'django',
    subtopic: 'models-migrationen',
    title: 'Migrationen erstellen und anwenden',
    description: 'Immer nach Änderungen an models.py.',
    language: 'terminal',
    code: 'python manage.py makemigrations\npython manage.py migrate',
  },
  {
    slug: 'admin-benutzer-anlegen',
    topic: 'django',
    subtopic: 'admin',
    title: 'Admin-Benutzer anlegen',
    description: 'Für den Login unter /admin.',
    language: 'terminal',
    code: 'python manage.py createsuperuser',
  },

  // Django REST Framework
  {
    slug: 'rest-framework-installieren',
    topic: 'django-rest-framework',
    subtopic: 'einrichtung',
    title: 'REST Framework installieren',
    description: 'Danach in settings.py bei INSTALLED_APPS eintragen.',
    language: 'terminal',
    code: 'pip install djangorestframework',
  },

  // Angular
  {
    slug: 'angular-cli-installieren',
    topic: 'angular',
    subtopic: 'cli',
    title: 'Angular CLI installieren',
    description: 'Einmalig pro Rechner.',
    language: 'terminal',
    code: 'npm install -g @angular/cli',
  },
  {
    slug: 'projekt-anlegen-und-starten',
    topic: 'angular',
    subtopic: 'cli',
    title: 'Neues Projekt anlegen und starten',
    description: '-o öffnet direkt den Browser auf localhost:4200.',
    language: 'terminal',
    code: 'ng new mein-projekt\ncd mein-projekt\nng serve -o',
  },
  {
    slug: 'komponente-und-service-erzeugen',
    topic: 'angular',
    subtopic: 'cli',
    title: 'Komponente und Service erzeugen',
    description: 'g c und g s sind die Kurzformen.',
    language: 'terminal',
    code: 'ng g c components/task-list\nng g s services/task',
  },
  {
    slug: 'fuer-veroeffentlichung-bauen',
    topic: 'angular',
    subtopic: 'build',
    title: 'Für die Veröffentlichung bauen',
    description: 'Ergebnis liegt in dist/ und kann auf den Server.',
    language: 'terminal',
    code: 'ng build',
  },

  // Server & Linux
  {
    slug: 'per-ssh-verbinden',
    topic: 'server',
    subtopic: 'verbindung',
    title: 'Per SSH verbinden',
    description: 'Ab Windows 10 direkt im Terminal möglich.',
    language: 'terminal',
    code: 'ssh benutzer@SERVER-IP',
  },
  {
    slug: 'datei-auf-server-kopieren',
    topic: 'server',
    subtopic: 'dateien-uebertragen',
    title: 'Datei auf den Server kopieren',
    description: 'Vom eigenen Rechner aus ausführen, nicht auf dem Server.',
    language: 'terminal',
    code: 'scp projekt.zip benutzer@SERVER-IP:/home/benutzer/',
  },
  {
    slug: 'server-aktualisieren',
    topic: 'server',
    subtopic: 'pakete',
    title: 'Server aktualisieren',
    description: 'Regelmäßig, und als Erstes auf einem neuen Server.',
    language: 'terminal',
    code: 'sudo apt update && sudo apt upgrade -y',
  },
  {
    slug: 'dienst-neu-starten',
    topic: 'server',
    subtopic: 'dienste-logs',
    title: 'Dienst neu starten und Status prüfen',
    description: 'Zum Beispiel nach einer Änderung an der Nginx-Konfiguration.',
    language: 'terminal',
    code: 'sudo nginx -t\nsudo systemctl restart nginx\nsudo systemctl status nginx',
  },
  {
    slug: 'logs-live-mitlesen',
    topic: 'server',
    subtopic: 'dienste-logs',
    title: 'Logs live mitlesen',
    description: 'Strg + C beendet die Ausgabe.',
    language: 'terminal',
    code: 'sudo journalctl -u gunicorn -f',
  },
  {
    slug: 'firewall-einrichten',
    topic: 'server',
    subtopic: 'firewall',
    title: 'Firewall einrichten',
    description: 'SSH zuerst erlauben, sonst sperrst du dich aus.',
    language: 'terminal',
    code: "sudo ufw allow OpenSSH\nsudo ufw allow 'Nginx Full'\nsudo ufw enable",
  },
  {
    slug: 'https-mit-lets-encrypt',
    topic: 'server',
    subtopic: 'https',
    title: 'HTTPS-Zertifikat mit Let’s Encrypt',
    description: 'Die Domain muss vorher auf den Server zeigen.',
    language: 'terminal',
    code: 'sudo apt install certbot python3-certbot-nginx\nsudo certbot --nginx -d meine-domain.de',
  },

  // Docker
  {
    slug: 'projekt-starten',
    topic: 'docker',
    subtopic: 'container',
    title: 'Projekt starten',
    description: 'Baut die Images neu und startet im Hintergrund.',
    language: 'terminal',
    code: 'docker compose up -d --build',
  },
  {
    slug: 'laufende-container',
    topic: 'docker',
    subtopic: 'container',
    title: 'Laufende Container anzeigen',
    description: 'Name, Status und Ports.',
    language: 'terminal',
    code: 'docker ps',
  },
  {
    slug: 'alles-stoppen',
    topic: 'docker',
    subtopic: 'container',
    title: 'Alles stoppen',
    description: 'Die Daten in Volumes bleiben erhalten.',
    language: 'terminal',
    code: 'docker compose down',
  },
  {
    slug: 'logs-ansehen',
    topic: 'docker',
    subtopic: 'fehlersuche',
    title: 'Logs ansehen',
    description: '-f folgt der Ausgabe live.',
    language: 'terminal',
    code: 'docker compose logs -f',
  },
  {
    slug: 'in-container-hineinschauen',
    topic: 'docker',
    subtopic: 'fehlersuche',
    title: 'In einen Container hineinschauen',
    description: 'Zum Beispiel, um dort migrate auszuführen.',
    language: 'terminal',
    code: 'docker compose exec web bash\n\n# oder direkt\ndocker compose exec web python manage.py migrate',
  },
];

@Service()
export class EntryApi {
  getByTopic(topic: string): Observable<Entry[]> {
    return of(ENTRIES.filter((entry) => entry.topic === topic));
  }

  getSummary(): Observable<{ entries: number; topics: number }> {
    return of({
      entries: ENTRIES.length,
      topics: new Set(ENTRIES.map((entry) => entry.topic)).size,
    });
  }
}
