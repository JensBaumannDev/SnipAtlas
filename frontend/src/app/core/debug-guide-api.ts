import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { ContentIndex, buildIndex } from './content-index';
import { DebugGuide } from './debug-guide';

const GUIDES: DebugGuide[] = [
  // General
  {
    slug: 'fehlermeldung-lesen',
    title: 'Eine Fehlermeldung richtig lesen',
    summary: 'Immer der erste Schritt: Die Meldung sagt meist schon, was los ist und wo.',
    steps: [
      {
        title: 'Die eigentliche Meldung finden',
        text: 'Fehlerausgaben sind oft lang. Die wichtige Zeile nennt die Art des Fehlers und eine kurze Beschreibung, zum Beispiel TypeError: … oder ModuleNotFoundError: …. In Python steht sie ganz unten, in der Browser-Konsole ganz oben.',
      },
      {
        title: 'Datei und Zeile suchen',
        text: 'Fast jede Meldung nennt eine Datei und eine Zeilennummer. Such in der Ausgabe nach der ersten Datei, die zu deinem eigenen Projekt gehört. Zeilen aus Paketen wie django oder node_modules überspringst du.',
      },
      {
        title: 'Die Meldung nachschlagen',
        text: 'Kopiere die Meldung ohne deine eigenen Pfade und Namen in die Suche von SnipAtlas oder in eine Suchmaschine. Sehr häufige Fehler findest du hier unter dem passenden Thema.',
      },
    ],
  },
  {
    slug: 'fehler-eingrenzen',
    title: 'Den Fehler eingrenzen',
    summary: 'Wenn unklar ist, an welcher Stelle etwas schiefgeht.',
    steps: [
      {
        title: 'Den Fehler gezielt auslösen',
        text: 'Finde die genauen Schritte, nach denen der Fehler jedes Mal auftritt. Erst wenn du ihn wiederholen kannst, kannst du prüfen, ob eine Änderung hilft.',
      },
      {
        title: 'Die letzte Änderung ansehen',
        text: 'Hat es vorher funktioniert, steckt der Fehler meist in dem, was du seitdem geändert hast. git diff zeigt alle Änderungen seit dem letzten Commit. Mit git stash legst du sie kurz beiseite und prüfst, ob der Fehler dann weg ist.',
        code: {
          language: 'terminal',
          code: 'git diff\n\n# Änderungen kurz beiseitelegen und wieder holen\ngit stash\ngit stash pop',
        },
      },
      {
        title: 'Werte ausgeben',
        text: 'Gib an verdächtigen Stellen aus, was wirklich in einer Variable steht. Oft ist ein Wert leer, hat einen anderen Typ oder kommt später an als gedacht.',
        code: { language: 'javascript', code: "console.log('task', task);" },
      },
      {
        title: 'Den Bereich halbieren',
        text: 'Kommentiere die Hälfte des verdächtigen Codes aus und prüfe, ob der Fehler bleibt. So weißt du, in welcher Hälfte er steckt, und wiederholst das, bis nur noch wenige Zeilen übrig sind.',
      },
    ],
  },
  {
    slug: 'browser-entwicklertools',
    title: 'Mit den Entwicklertools im Browser debuggen',
    summary: 'Wenn die Seite nicht anzeigt oder lädt, was sie soll.',
    steps: [
      {
        title: 'Entwicklertools öffnen',
        text: 'Unter Windows öffnest du sie mit F12 oder Strg + Umschalt + I, auf dem Mac mit Cmd + Option + I. Am besten öffnest du sie, bevor du die Seite neu lädst.',
      },
      {
        title: 'Die Konsole lesen',
        text: 'Im Reiter Konsole stehen Fehler rot. Ein Klick auf den Dateinamen rechts daneben springt direkt zur Stelle im Code.',
      },
      {
        title: 'Anfragen im Netzwerk-Reiter prüfen',
        text: 'Der Reiter Netzwerk zeigt jede Anfrage an das Backend. Ein Status ab 400 heißt Fehler: 401 nicht angemeldet, 404 falsche Adresse, 500 Fehler im Backend. Klick auf die Anfrage und sieh dir unter Antwort an, was zurückkam.',
      },
      {
        title: 'HTML und CSS live ansehen',
        text: 'Im Reiter Elemente siehst du das HTML so, wie der Browser es gerade anzeigt, und daneben alle CSS-Regeln. Änderungen dort wirken sofort, verschwinden aber beim Neuladen.',
      },
    ],
  },

  // Python
  {
    slug: 'python-traceback',
    topic: 'python',
    title: 'Python: Traceback lesen und Werte prüfen',
    summary: 'Wenn ein Python-Skript mit einem Fehler abbricht.',
    steps: [
      {
        title: 'Den Traceback von unten lesen',
        text: 'Die letzte Zeile nennt den Fehler. Darüber steht, über welche Aufrufe es dazu kam. Die unterste Zeile mit einer Datei aus deinem Projekt ist meist die Stelle, an der du suchen musst.',
      },
      {
        title: 'Werte mit print ausgeben',
        text: 'Mit = in den geschweiften Klammern gibt ein f-String Name und Wert zusammen aus. So siehst du sofort, welche Variable welchen Wert hat.',
        code: { language: 'python', code: 'print(f"{task=}")\nprint(f"{type(task)=}")' },
      },
      {
        title: 'Mit breakpoint() anhalten',
        text: 'breakpoint() hält das Programm an dieser Stelle an. Im Terminal kannst du dann Variablen ansehen: p name zeigt einen Wert, n geht zur nächsten Zeile, c läuft weiter, q beendet.',
        code: {
          language: 'python',
          code: 'def brutto(netto):\n    breakpoint()\n    return netto * 1.19',
        },
      },
    ],
  },

  // Django
  {
    slug: 'django-fehler-finden',
    topic: 'django',
    title: 'Django: Fehler finden',
    summary: 'Wenn eine Seite einen Fehler zeigt oder der Server nicht startet.',
    steps: [
      {
        title: 'Die Ausgabe von runserver lesen',
        text: 'Jede Anfrage und jeder Fehler erscheint im Terminal, in dem der Server läuft. Dort steht der vollständige Traceback, auch wenn der Browser nur „Server Error (500)“ zeigt.',
      },
      {
        title: 'Die Fehlerseite im Browser nutzen',
        text: 'Steht DEBUG = True in settings.py, zeigt Django eine gelbe Fehlerseite mit Traceback und allen Werten. Online muss DEBUG immer False sein, sonst sieht jeder diese Details.',
      },
      {
        title: 'Das Projekt prüfen lassen',
        text: 'check findet typische Fehler in den Einstellungen und Models, ohne dass du eine Seite aufrufen musst.',
        code: { language: 'terminal', code: 'python manage.py check' },
      },
      {
        title: 'In der Shell ausprobieren',
        text: 'In der Django-Shell kannst du Models und Abfragen direkt testen, zum Beispiel ob ein Datensatz wirklich existiert.',
        code: { language: 'terminal', code: 'python manage.py shell' },
      },
    ],
  },

  // Django REST Framework
  {
    slug: 'api-anfragen-pruefen',
    topic: 'django-rest-framework',
    title: 'Django REST Framework: API-Anfragen prüfen',
    summary: 'Wenn das Frontend keine oder falsche Daten bekommt.',
    steps: [
      {
        title: 'Den Endpunkt im Browser öffnen',
        text: 'Ruf die Adresse direkt im Browser auf, zum Beispiel http://127.0.0.1:8000/api/tasks/. Django REST Framework zeigt eine lesbare Seite mit den Daten oder der Fehlermeldung.',
      },
      {
        title: 'Die Anfrage im Terminal senden',
        text: 'curl zeigt Status, Header und Antwort ohne Frontend dazwischen. Funktioniert es hier, liegt der Fehler im Frontend. Unter Windows nimmst du curl.exe, weil curl in PowerShell etwas anderes ist.',
        code: {
          language: 'terminal',
          code: {
            win: 'curl.exe -i http://127.0.0.1:8000/api/tasks/',
            unix: 'curl -i http://127.0.0.1:8000/api/tasks/',
          },
        },
      },
      {
        title: 'Den Status deuten',
        text: '400 heißt, die gesendeten Daten passen nicht zum Serializer, die Antwort nennt das Feld. 401 und 403 heißen, Login oder Rechte fehlen. 404 heißt, die Adresse stimmt nicht, oft fehlt der Schrägstrich am Ende.',
      },
    ],
  },

  // JavaScript
  {
    slug: 'javascript-console-debugger',
    topic: 'javascript',
    title: 'JavaScript: Mit console und debugger arbeiten',
    summary: 'Wenn ein Skript nicht tut, was es soll, aber keinen Fehler zeigt.',
    steps: [
      {
        title: 'Werte übersichtlich ausgeben',
        text: 'console.log zeigt einen Wert, console.table zeigt Arrays aus Objekten als Tabelle. Ein kurzer Text davor hilft, die Ausgaben auseinanderzuhalten.',
        code: {
          language: 'javascript',
          code: "console.log('Antwort', data);\nconsole.table(tasks);",
        },
      },
      {
        title: 'Mit debugger anhalten',
        text: 'Steht debugger im Code und sind die Entwicklertools offen, hält der Browser genau dort an. Du siehst alle Variablen und gehst Zeile für Zeile weiter.',
        code: {
          language: 'javascript',
          code: 'function save(task) {\n  debugger;\n  tasks.push(task);\n}',
        },
      },
    ],
  },

  // Angular
  {
    slug: 'angular-fehler-finden',
    topic: 'angular',
    title: 'Angular: Fehler finden',
    summary: 'Wenn die App nicht baut oder im Browser nichts anzeigt.',
    steps: [
      {
        title: 'Das Terminal von ng serve lesen',
        text: 'Fehler beim Bauen, etwa falsche Typen oder fehlende Imports, erscheinen im Terminal und als Overlay im Browser. Sie nennen Datei und Zeile.',
      },
      {
        title: 'Laufzeitfehler in der Konsole lesen',
        text: 'Fehler, die erst beim Benutzen auftreten, stehen in der Browser-Konsole. Beginnt die Meldung mit einem Code wie NG0100, findest du eine Erklärung unter angular.dev/errors.',
      },
      {
        title: 'Signals und Werte prüfen',
        text: 'Gib im Template oder in der Komponente aus, was wirklich ankommt. Die json-Pipe zeigt ganze Objekte lesbar an.',
        code: { language: 'html', code: '<pre>{{ tasks() | json }}</pre>' },
      },
      {
        title: 'Angular DevTools nutzen',
        text: 'Die Browser-Erweiterung Angular DevTools zeigt den Komponentenbaum mit allen Inputs und Signals. So siehst du, welche Komponente welche Daten hat.',
      },
    ],
  },

  // Git
  {
    slug: 'git-aenderungen-finden',
    topic: 'git',
    title: 'Git: Herausfinden, was sich geändert hat',
    summary: 'Wenn etwas nicht mehr funktioniert und du wissen willst, seit wann.',
    steps: [
      {
        title: 'Den aktuellen Stand prüfen',
        text: 'git status zeigt den Branch und alle geänderten Dateien. git diff zeigt, was sich genau geändert hat.',
        code: { language: 'terminal', code: 'git status\ngit diff' },
      },
      {
        title: 'Den Verlauf einer Datei ansehen',
        text: 'Mit -p zeigt git log zu jedem Commit auch die Änderungen an dieser Datei.',
        code: { language: 'terminal', code: 'git log --oneline -p -- src/app/app.ts' },
      },
      {
        title: 'Einen alten Stand ausprobieren',
        text: 'Mit git switch --detach springst du zu einem älteren Commit und prüfst, ob der Fehler dort schon da war. git switch - bringt dich zurück.',
        code: { language: 'terminal', code: 'git switch --detach a1b2c3d\ngit switch -' },
      },
    ],
  },

  // Docker
  {
    slug: 'docker-container-pruefen',
    topic: 'docker',
    title: 'Docker: Container prüfen',
    summary: 'Wenn ein Container nicht startet oder immer wieder neu startet.',
    steps: [
      {
        title: 'Den Status ansehen',
        text: 'ps zeigt jeden Container mit Status. Steht dort Exited oder Restarting, ist der Container abgestürzt.',
        code: { language: 'terminal', code: 'docker compose ps' },
      },
      {
        title: 'Die Logs lesen',
        text: 'Die Logs zeigen die Ausgabe des Programms im Container, also auch den Fehler, an dem es abgebrochen ist.',
        code: { language: 'terminal', code: 'docker compose logs web' },
      },
      {
        title: 'Im Container nachsehen',
        text: 'Mit exec öffnest du eine Shell im laufenden Container und prüfst, ob Dateien und Umgebungsvariablen stimmen.',
        code: { language: 'terminal', code: 'docker compose exec web bash\nenv' },
      },
    ],
  },
];

@Service()
export class DebugGuideApi {
  getAll(): Observable<DebugGuide[]> {
    return of(GUIDES);
  }

  getGeneral(): Observable<DebugGuide[]> {
    return of(GUIDES.filter((guide) => !guide.topic));
  }

  getByTopic(topic: string): Observable<DebugGuide[]> {
    return of(GUIDES.filter((guide) => guide.topic === topic));
  }

  getIndex(): Observable<ContentIndex> {
    return of(buildIndex(GUIDES.flatMap((guide) => (guide.topic ? [{ topic: guide.topic }] : []))));
  }
}
