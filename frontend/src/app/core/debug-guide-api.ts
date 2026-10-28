import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { ContentIndex, buildIndex } from './content-index';
import { DebugGuide } from './debug-guide';

const GUIDES: DebugGuide[] = [
  // Ways to debug
  {
    slug: 'vorgehen',
    label: 'Vorgehen',
    title: 'Der Ablauf bei jedem Fehler',
    summary: 'Diese vier Schritte helfen bei jedem Fehler, egal in welcher Sprache.',
    steps: [
      {
        title: 'Die Meldung lesen',
        text: 'Die wichtige Zeile nennt die Art des Fehlers und eine kurze Beschreibung, zum Beispiel TypeError: … oder ModuleNotFoundError: …. In Python steht sie ganz unten, in der Browser-Konsole ganz oben. Daneben stehen meist Datei und Zeile. Such die erste Datei, die zu deinem eigenen Projekt gehört, und überspring Zeilen aus Paketen wie django oder node_modules.',
      },
      {
        title: 'Den Fehler nachstellen',
        text: 'Finde die genauen Schritte, nach denen der Fehler jedes Mal auftritt. Erst wenn du ihn wiederholen kannst, kannst du prüfen, ob eine Änderung hilft.',
      },
      {
        title: 'Den Fehler eingrenzen',
        text: 'Hat es vorher funktioniert, steckt der Fehler meist in deiner letzten Änderung. git diff zeigt sie dir, mit git stash legst du sie kurz beiseite. Hilft das nicht, kommentierst du die Hälfte des verdächtigen Codes aus und prüfst, in welcher Hälfte der Fehler steckt.',
        code: {
          language: 'terminal',
          code: 'git diff\n\n# Änderungen kurz beiseitelegen und wieder holen\ngit stash\ngit stash pop',
        },
      },
      {
        title: 'Beheben und prüfen',
        text: 'Ändere immer nur eine Sache und prüf danach, ob der Fehler weg ist und alles andere noch funktioniert. Kommst du nicht weiter, schlag die Meldung ohne deine eigenen Pfade und Namen nach, hier in der Suche oder unter dem passenden Thema.',
      },
    ],
  },
  {
    slug: 'browser',
    label: 'Browser',
    title: 'Mit den Entwicklertools im Browser debuggen',
    summary: 'Wenn die Seite falsch aussieht, nicht lädt oder Daten fehlen.',
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
  {
    slug: 'terminal',
    label: 'Terminal',
    title: 'Mit Ausgaben im Terminal debuggen',
    summary: 'Wenn der Server abbricht oder du sehen willst, was eine Variable enthält.',
    steps: [
      {
        title: 'Die Ausgabe des Servers lesen',
        text: 'Das Terminal, in dem ng serve oder runserver läuft, zeigt Fehler beim Starten und bei jeder Anfrage. Scroll nach oben bis zur ersten roten Meldung. Alles danach sind oft nur Folgefehler.',
      },
      {
        title: 'Werte ausgeben',
        text: 'Gib an der verdächtigen Stelle aus, was wirklich in einer Variable steht. Oft ist ein Wert leer, hat einen anderen Typ oder kommt später an als gedacht. print landet im Terminal des Servers, console.log in der Browser-Konsole.',
        code: { language: 'python', code: "print('task', task)" },
      },
      {
        title: 'Ausgaben wieder entfernen',
        text: 'Lösch die Ausgaben, sobald du den Fehler gefunden hast. Sonst füllen sie später das Terminal und zeigen unter Umständen Daten, die dort nichts zu suchen haben.',
      },
    ],
  },
  {
    slug: 'debugger',
    label: 'Debugger',
    title: 'Mit Haltepunkten debuggen',
    summary: 'Wenn du Zeile für Zeile sehen willst, was der Code macht.',
    steps: [
      {
        title: 'Einen Haltepunkt setzen',
        text: 'Ein Haltepunkt hält das Programm an einer Zeile an. In VS Code und in den Entwicklertools im Reiter Quellen klickst du dafür links neben die Zeilennummer. In Python schreibst du breakpoint() an die Stelle.',
        code: { language: 'python', code: 'breakpoint()' },
      },
      {
        title: 'Werte ansehen',
        text: 'Steht das Programm, siehst du alle Variablen mit ihrem aktuellen Wert. Im Python-Debugger gibst du dafür einfach den Namen der Variable ein.',
      },
      {
        title: 'Schritt für Schritt weiter',
        text: 'Von dort gehst du Zeile für Zeile weiter und siehst, wo ein Wert anders wird als erwartet.',
        code: {
          language: 'python',
          code: 'n  # nächste Zeile\nc  # weiterlaufen lassen\nq  # Debugger beenden',
        },
      },
    ],
  },
  {
    slug: 'tests',
    label: 'Tests',
    title: 'Mit Tests debuggen',
    summary: 'Wenn ein Fehler nicht wiederkommen soll.',
    steps: [
      {
        title: 'Den Fehler in einem Test nachstellen',
        text: 'Schreib einen Test, der genau das prüft, was gerade falsch läuft. Er muss zuerst fehlschlagen. Dann weißt du, dass er den Fehler wirklich erwischt.',
      },
      {
        title: 'Den Fehler beheben',
        text: 'Ändere den Code, bis der Test durchläuft. Du musst dafür nicht jedes Mal im Browser klicken, der Test prüft es in Sekunden.',
        code: {
          language: 'terminal',
          code: { win: 'python manage.py test', unix: 'python3 manage.py test' },
        },
      },
      {
        title: 'Den Test behalten',
        text: 'Der Test bleibt im Projekt. Taucht der Fehler durch eine spätere Änderung wieder auf, schlägt er sofort an.',
      },
    ],
  },
  {
    slug: 'ki',
    label: 'KI',
    title: 'Die KI richtig fragen',
    summary: 'Wenn du nicht weiterkommst, die Lösung aber verstehen willst.',
    steps: [
      {
        title: 'Genug Zusammenhang mitgeben',
        text: 'Gib die vollständige Fehlermeldung, den passenden Code-Ausschnitt und dazu, was du erwartet hast und was stattdessen passiert. Je genauer die Frage, desto besser die Antwort.',
      },
      {
        title: 'Keine geheimen Daten einfügen',
        text: 'Passwörter, API-Schlüssel und den Inhalt deiner .env-Datei gibst du nie weiter. Ersetze sie vorher durch Platzhalter.',
      },
      {
        title: 'Die Antwort prüfen',
        text: 'Eine KI klingt auch dann sicher, wenn sie falsch liegt. Lass dir erklären, warum die Lösung funktioniert, und übernimm nur Code, den du verstehst. Danach prüfst du wie immer, ob der Fehler wirklich weg ist.',
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

  getWay(slug: string): Observable<DebugGuide | undefined> {
    return of(GUIDES.find((guide) => !guide.topic && guide.slug === slug));
  }

  getByTopic(topic: string): Observable<DebugGuide[]> {
    return of(GUIDES.filter((guide) => guide.topic === topic));
  }

  getIndex(): Observable<ContentIndex> {
    return of(buildIndex(GUIDES.flatMap((guide) => (guide.topic ? [{ topic: guide.topic }] : []))));
  }
}
