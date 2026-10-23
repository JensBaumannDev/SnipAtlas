import { Service } from '@angular/core';
import { Observable, of } from 'rxjs';
import { Concept } from './concept';

const CONCEPTS: Concept[] = [
  // HTML
  {
    slug: 'grundgeruest-einer-seite',
    topic: 'html',
    subtopic: 'grundgeruest',
    title: 'Grundgerüst einer Seite',
    summary: 'Der Rahmen, den jede HTML-Seite braucht.',
    explanation:
      'DOCTYPE sagt dem Browser, dass es sich um modernes HTML handelt. In head stehen Angaben über die Seite wie Zeichensatz, Titel und eingebundene Dateien, in body der sichtbare Inhalt. Das Script steht am Ende von body, damit zuerst die Seite geladen wird.',
    language: 'html',
    code: '<!DOCTYPE html>\n<html lang="de">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n  <title>Meine Seite</title>\n  <link rel="stylesheet" href="style.css">\n</head>\n<body>\n\n  <script src="script.js"></script>\n</body>\n</html>',
    note: 'Ohne meta viewport zeigt das Handy die Seite verkleinert an, als wäre es ein großer Bildschirm.',
  },
  {
    slug: 'semantische-struktur',
    topic: 'html',
    subtopic: 'grundgeruest',
    title: 'Semantische Struktur',
    summary: 'Bereiche der Seite mit passenden Elementen auszeichnen.',
    explanation:
      'header, nav, main, section und footer sagen, welche Aufgabe ein Bereich hat. Screenreader und Suchmaschinen verstehen die Seite dadurch besser als bei lauter div-Elementen.',
    language: 'html',
    code: '<header>…</header>\n<nav>…</nav>\n<main>\n  <section>…</section>\n</main>\n<footer>…</footer>',
    note: 'main gibt es nur einmal pro Seite.',
  },
  {
    slug: 'link-und-bild',
    topic: 'html',
    subtopic: 'elemente',
    title: 'Link und Bild',
    summary: 'Auf andere Seiten verweisen und Bilder einbinden.',
    explanation:
      'href gibt das Ziel des Links an. Beim Bild steht die Datei in src. alt beschreibt das Bild für Screenreader und erscheint, wenn das Bild nicht lädt.',
    language: 'html',
    code: '<a href="https://example.com" target="_blank">Zur Seite</a>\n\n<img src="bild.jpg" alt="Beschreibung des Bildes">',
    note: 'target="_blank" öffnet einen neuen Tab. Rein dekorative Bilder bekommen ein leeres alt="".',
  },
  {
    slug: 'formular-mit-label',
    topic: 'html',
    subtopic: 'formulare',
    title: 'Formular mit Label',
    summary: 'Eingabefelder richtig beschriften.',
    explanation:
      'for beim label und id beim Feld gehören zusammen. Ein Klick auf das Label setzt dann den Cursor ins Feld, und Screenreader lesen die Beschriftung vor.',
    language: 'html',
    code: '<form>\n  <label for="email">E-Mail</label>\n  <input id="email" type="email" required>\n  <button type="submit">Senden</button>\n</form>',
    note: 'Ein Platzhalter ersetzt kein Label. Er verschwindet, sobald man tippt.',
  },

  // CSS
  {
    slug: 'mittig-zentrieren',
    topic: 'css',
    subtopic: 'flexbox',
    title: 'Mittig zentrieren mit Flexbox',
    summary: 'Ein Element waagerecht und senkrecht in die Mitte setzen.',
    explanation:
      'display: flex macht die Box zum Flex-Container. justify-content richtet die Kinder auf der Hauptachse aus, align-items auf der Querachse.',
    language: 'css',
    code: '.box {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n  min-height: 300px;\n}',
    note: 'Senkrecht zentrieren klappt nur, wenn der Container höher ist als sein Inhalt, zum Beispiel mit min-height.',
  },
  {
    slug: 'responsives-raster',
    topic: 'css',
    subtopic: 'grid',
    title: 'Responsives Raster',
    summary: 'So viele Spalten wie passen, ohne Media Query.',
    explanation:
      'repeat(auto-fill, …) legt so viele Spalten an, wie in die Breite passen. minmax(250px, 1fr) sorgt dafür, dass jede Spalte mindestens 250px breit ist und sich den restlichen Platz teilt.',
    language: 'css',
    code: '.grid {\n  display: grid;\n  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));\n  gap: 16px;\n}',
    note: 'Mit auto-fit statt auto-fill dehnen sich wenige Elemente über die ganze Breite.',
  },
  {
    slug: 'media-query',
    topic: 'css',
    subtopic: 'responsive',
    title: 'Media Query',
    summary: 'Regeln nur für bestimmte Bildschirmbreiten.',
    explanation:
      'Was in @media (max-width: 600px) steht, gilt nur, solange das Fenster höchstens 600px breit ist. So passt du das Layout ans Handy an.',
    language: 'css',
    code: '.menu {\n  display: flex;\n}\n\n@media (max-width: 600px) {\n  .menu {\n    flex-direction: column;\n  }\n}',
    note: 'Die Media Query steht unter den normalen Regeln, sonst überschreiben diese sie wieder.',
  },

  // JavaScript
  {
    slug: 'for-of',
    topic: 'javascript',
    subtopic: 'schleifen',
    title: 'for...of-Schleife',
    summary: 'Jedes Element eines Arrays durchlaufen.',
    explanation:
      'for...of nimmt nacheinander jeden Wert aus einem Array und führt den Block in den geschweiften Klammern einmal pro Wert aus. Mit const bekommt jeder Durchlauf eine eigene Variable.',
    language: 'javascript',
    code: "const namen = ['Anna', 'Ben', 'Cem'];\n\nfor (const name of namen) {\n  console.log(`Hallo ${name}`);\n}",
    note: 'for...in durchläuft die Schlüssel, bei Arrays also die Indizes als Text. Für die Werte eines Arrays nimmst du for...of.',
  },
  {
    slug: 'map-foreach',
    topic: 'javascript',
    subtopic: 'arrays',
    title: 'map und forEach',
    summary: 'Mit jedem Element etwas tun oder ein neues Array bauen.',
    explanation:
      'Beide rufen eine Funktion für jedes Element auf. map sammelt die Rückgabewerte in einem neuen Array, das alte bleibt unverändert. forEach gibt nichts zurück und eignet sich für Ausgaben oder Nebenwirkungen.',
    language: 'javascript',
    code: 'const preise = [10, 20, 30];\n\nconst brutto = preise.map((preis) => preis * 1.19);\npreise.forEach((preis) => console.log(preis));',
    note: 'Brauchst du ein Ergebnis, nimm map. Ein forEach mit push in ein leeres Array ist fast immer ein map.',
  },
  {
    slug: 'async-await',
    topic: 'javascript',
    subtopic: 'async',
    title: 'async und await',
    summary: 'Auf eine Antwort warten, ohne die Seite zu blockieren.',
    explanation:
      'Eine async-Funktion gibt immer ein Promise zurück. Mit await wartet sie an dieser Stelle, bis das Promise fertig ist, und arbeitet dann mit dem Ergebnis weiter. Fehler fängst du wie gewohnt mit try und catch.',
    language: 'javascript',
    code: "async function ladeAufgaben() {\n  try {\n    const antwort = await fetch('/api/tasks/');\n    if (!antwort.ok) {\n      throw new Error(`Status ${antwort.status}`);\n    }\n    return await antwort.json();\n  } catch (fehler) {\n    console.error(fehler);\n  }\n}",
    note: 'fetch wirft bei 404 oder 500 keinen Fehler. Prüfe deshalb immer antwort.ok.',
  },

  {
    slug: 'for-mit-zaehler',
    topic: 'javascript',
    subtopic: 'schleifen',
    title: 'for-Schleife mit Zähler',
    summary: 'Eine Schleife, bei der du den Index brauchst.',
    explanation:
      'Die drei Teile in der Klammer sind Start, Bedingung und Schritt. Die Schleife läuft, solange die Bedingung wahr ist, und erhöht i nach jedem Durchlauf.',
    language: 'javascript',
    code: 'for (let i = 0; i < 5; i++) {\n  console.log(i);\n}',
    note: 'Brauchst du nur die Werte eines Arrays, ist for...of lesbarer.',
  },
  {
    slug: 'filter-find',
    topic: 'javascript',
    subtopic: 'arrays',
    title: 'filter und find',
    summary: 'Elemente aussortieren oder das erste passende finden.',
    explanation:
      'filter gibt ein neues Array mit allen Elementen zurück, für die die Funktion true liefert. find gibt nur das erste passende Element zurück.',
    language: 'javascript',
    code: 'const preise = [10, 20, 30];\n\nconst teuer = preise.filter((preis) => preis > 15); // [20, 30]\nconst erstes = preise.find((preis) => preis > 15); // 20',
    note: 'Findet find nichts, ist das Ergebnis undefined.',
  },
  {
    slug: 'template-strings',
    topic: 'javascript',
    subtopic: 'strings',
    title: 'Template-Strings',
    summary: 'Variablen direkt in Text einsetzen.',
    explanation:
      'Text in Backticks darf Platzhalter mit ${…} enthalten. Darin kann jede Variable oder Rechnung stehen.',
    language: 'javascript',
    code: "const name = 'Jens';\nconsole.log(`Hallo ${name}, du hast ${3 + 2} Aufgaben.`);",
    note: 'Template-Strings dürfen auch über mehrere Zeilen gehen.',
  },
  {
    slug: 'objekt-durchlaufen',
    topic: 'javascript',
    subtopic: 'objekte',
    title: 'Über ein Objekt laufen',
    summary: 'Schlüssel und Wert eines Objekts gemeinsam durchgehen.',
    explanation:
      'Object.entries macht aus einem Objekt ein Array aus Paaren [Schlüssel, Wert]. for...of mit eckigen Klammern zerlegt jedes Paar direkt in zwei Variablen.',
    language: 'javascript',
    code: "const user = { name: 'Jens', role: 'dev' };\n\nfor (const [key, value] of Object.entries(user)) {\n  console.log(key, value);\n}",
  },

  // TypeScript
  {
    slug: 'interface',
    topic: 'typescript',
    subtopic: 'interfaces',
    title: 'Interface',
    summary: 'Festlegen, welche Felder ein Objekt hat.',
    explanation:
      'Ein Interface beschreibt die Form eines Objekts: welche Felder es gibt und welchen Typ sie haben. Fehlt ein Feld oder hat es den falschen Typ, meldet der Editor das schon beim Schreiben.',
    language: 'typescript',
    code: "interface Task {\n  id: number;\n  title: string;\n  done: boolean;\n  dueDate?: string;\n}\n\nconst task: Task = { id: 1, title: 'Lernen', done: false };",
    note: 'Das ? macht ein Feld optional. Im fertigen JavaScript gibt es keine Interfaces mehr, sie helfen nur beim Entwickeln.',
  },

  {
    slug: 'typen-fuer-variablen',
    topic: 'typescript',
    subtopic: 'typen',
    title: 'Typen für Variablen',
    summary: 'Festlegen, welche Art Wert eine Variable hat.',
    explanation:
      'Der Typ steht nach dem Doppelpunkt. Weist du später einen falschen Wert zu, meldet der Editor das sofort.',
    language: 'typescript',
    code: "let title: string = 'Einkaufen';\nlet count: number = 3;\nlet done: boolean = false;\nlet tags: string[] = ['haus', 'dringend'];",
    note: 'Ist der Typ offensichtlich, erkennt TypeScript ihn selbst: let count = 3 ist schon number.',
  },
  {
    slug: 'union-typ',
    topic: 'typescript',
    subtopic: 'typen',
    title: 'Union-Typ',
    summary: 'Nur bestimmte Werte erlauben.',
    explanation:
      'Mit | zählst du die erlaubten Werte auf. Ein Tippfehler wie "erledig" fällt so schon im Editor auf.',
    language: 'typescript',
    code: "type Status = 'offen' | 'erledigt' | 'archiviert';\n\nlet status: Status = 'offen';",
  },
  {
    slug: 'funktion-mit-typen',
    topic: 'typescript',
    subtopic: 'funktionen',
    title: 'Funktion mit Typen',
    summary: 'Typen für Parameter und Rückgabewert.',
    explanation:
      'Jeder Parameter bekommt seinen Typ, der Rückgabetyp steht nach der Klammer. Rufst du die Funktion mit falschen Werten auf, meldet der Editor den Fehler.',
    language: 'typescript',
    code: 'function add(a: number, b: number): number {\n  return a + b;\n}\n\nconst greet = (name: string): string => `Hallo ${name}`;',
  },

  // Angular
  {
    slug: 'input-output',
    topic: 'angular',
    subtopic: 'komponenten',
    title: 'input und output',
    summary: 'Daten in eine Komponente geben und Ereignisse zurückmelden.',
    explanation:
      'Die Eltern-Komponente gibt Daten über ein input hinein und hört über ein output auf Ereignisse. Im Template der Eltern sieht das so aus: <app-task-item [title]="task.title" (removed)="remove(task)" />.',
    language: 'typescript',
    code: "import { Component, input, output } from '@angular/core';\n\n@Component({\n  selector: 'app-task-item',\n  templateUrl: './task-item.html',\n})\nexport class TaskItem {\n  readonly title = input.required<string>();\n  readonly removed = output<void>();\n}",
    note: 'Ein input ist ein Signal. Im Template schreibst du deshalb title(), nicht title.',
  },
  {
    slug: 'signal-computed',
    topic: 'angular',
    subtopic: 'signals',
    title: 'signal und computed',
    summary: 'Zustand speichern und davon abgeleitete Werte berechnen.',
    explanation:
      'Ein signal hält einen Wert. Mit set ersetzt du ihn, mit update berechnest du ihn aus dem alten Wert. computed leitet einen Wert aus anderen Signals ab und rechnet automatisch neu, wenn sich einer davon ändert.',
    language: 'typescript',
    code: "import { computed, signal } from '@angular/core';\n\nconst anzahl = signal(0);\nconst doppelt = computed(() => anzahl() * 2);\n\nanzahl.set(5);\nanzahl.update((wert) => wert + 1);\nconsole.log(doppelt()); // 12",
    note: 'Ein Signal liest du mit Klammern: anzahl(). Ohne Klammern bekommst du das Signal selbst, nicht seinen Wert.',
  },

  {
    slug: 'for-im-template',
    topic: 'angular',
    subtopic: 'templates',
    title: '@for im Template',
    summary: 'Eine Liste im Template ausgeben.',
    explanation:
      '@for wiederholt den Block für jedes Element. track sagt Angular, woran es ein Element wiedererkennt, damit nur geänderte Einträge neu gezeichnet werden. @empty erscheint, wenn die Liste leer ist.',
    language: 'html',
    code: '@for (task of tasks; track task.id) {\n  <li>{{ task.title }}</li>\n} @empty {\n  <li>Keine Aufgaben</li>\n}',
    note: 'track ist Pflicht. Hat jedes Element eine id, nimm sie.',
  },
  {
    slug: 'if-im-template',
    topic: 'angular',
    subtopic: 'templates',
    title: '@if im Template',
    summary: 'Etwas nur unter einer Bedingung anzeigen.',
    explanation:
      '@if zeigt den Block nur, wenn die Bedingung wahr ist, sonst den @else-Block. Es ersetzt das ältere *ngIf.',
    language: 'html',
    code: '@if (isLoggedIn) {\n  <app-dashboard />\n} @else {\n  <app-login />\n}',
  },
  {
    slug: 'httpclient-im-service',
    topic: 'angular',
    subtopic: 'services-http',
    title: 'HttpClient im Service',
    summary: 'Daten vom Backend laden.',
    explanation:
      'provideHttpClient stellt den HttpClient einmal für die ganze App bereit. Ein Service holt ihn mit inject und gibt die Anfrage als Observable zurück.',
    language: 'typescript',
    code: "// app.config.ts\nproviders: [provideHttpClient()]\n\n// task.service.ts\n@Injectable({ providedIn: 'root' })\nexport class TaskService {\n  private http = inject(HttpClient);\n\n  getTasks() {\n    return this.http.get<Task[]>('http://127.0.0.1:8000/api/tasks/');\n  }\n}",
    note: 'Die Anfrage startet erst, wenn jemand das Observable abonniert, zum Beispiel mit subscribe oder toSignal.',
  },

  // Python
  {
    slug: 'for-schleife',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'for-Schleife',
    summary: 'Jedes Element einer Liste durchlaufen.',
    explanation:
      'Die for-Schleife nimmt nacheinander jedes Element aus einer Liste und führt den eingerückten Block einmal pro Element aus. Die Variable nach for enthält dabei das aktuelle Element.',
    language: 'python',
    code: 'namen = ["Anna", "Ben", "Cem"]\n\nfor name in namen:\n    print(f"Hallo {name}")',
    note: 'Was zur Schleife gehört, erkennt Python an der Einrückung. Fehlt sie, gibt es einen IndentationError.',
  },
  {
    slug: 'range',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'Zählen mit range()',
    summary: 'Eine Schleife eine bestimmte Anzahl Male laufen lassen.',
    explanation:
      'range(stop) erzeugt die Zahlen von 0 bis vor stop. Mit range(start, stop, schritt) legst du Anfang und Schrittweite selbst fest.',
    language: 'python',
    code: 'for i in range(5):\n    print(i)  # 0, 1, 2, 3, 4\n\nfor i in range(2, 10, 2):\n    print(i)  # 2, 4, 6, 8',
    note: 'range(5) zählt von 0 bis 4. Die 5 selbst ist nicht dabei.',
  },
  {
    slug: 'while-schleife',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'while-Schleife',
    summary: 'Wiederholen, solange eine Bedingung gilt.',
    explanation:
      'Die while-Schleife prüft vor jedem Durchlauf ihre Bedingung. Ist sie wahr, läuft der Block noch einmal. Sie passt, wenn du vorher nicht weißt, wie oft wiederholt werden muss.',
    language: 'python',
    code: 'versuche = 0\n\nwhile versuche < 3:\n    print(f"Versuch {versuche + 1}")\n    versuche += 1',
    note: 'Wird die Bedingung nie falsch, läuft die Schleife endlos. Im Terminal brichst du mit Strg + C ab.',
  },
  {
    slug: 'break-continue',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'break und continue',
    summary: 'Eine Schleife abbrechen oder einen Durchlauf überspringen.',
    explanation:
      'break beendet die Schleife sofort. continue springt zum nächsten Durchlauf, der Rest des Blocks wird übersprungen.',
    language: 'python',
    code: 'for zahl in [3, 8, -1, 5]:\n    if zahl < 0:\n        break\n    if zahl % 2 == 0:\n        continue\n    print(zahl)  # nur 3',
    note: 'break und continue wirken nur auf die innerste Schleife.',
  },
  {
    slug: 'enumerate',
    topic: 'python',
    subtopic: 'schleifen',
    title: 'Mitzählen mit enumerate()',
    summary: 'Beim Durchlaufen auch die Nummer des Elements bekommen.',
    explanation:
      'enumerate liefert bei jedem Durchlauf zwei Werte: die Nummer und das Element. So brauchst du keinen eigenen Zähler.',
    language: 'python',
    code: 'aufgaben = ["Einkaufen", "Sport", "Lernen"]\n\nfor nummer, aufgabe in enumerate(aufgaben, start=1):\n    print(f"{nummer}. {aufgabe}")',
    note: 'Ohne start beginnt enumerate bei 0.',
  },
  {
    slug: 'liste-aendern',
    topic: 'python',
    subtopic: 'listen',
    title: 'Listen anlegen und ändern',
    summary: 'Mehrere Werte in einer Variable sammeln.',
    explanation:
      'Eine Liste steht in eckigen Klammern. Mit append hängst du ein Element hinten an, mit remove entfernst du eins, len gibt die Anzahl zurück.',
    language: 'python',
    code: 'farben = ["rot", "grün"]\nfarben.append("blau")\nfarben.remove("rot")\n\nprint(farben)       # [\'grün\', \'blau\']\nprint(len(farben))  # 2',
    note: 'remove löscht nur das erste passende Element und wirft einen ValueError, wenn es fehlt.',
  },
  {
    slug: 'index-slicing',
    topic: 'python',
    subtopic: 'listen',
    title: 'Index und Slicing',
    summary: 'Einzelne Elemente oder Ausschnitte einer Liste holen.',
    explanation:
      'Mit einer Zahl in eckigen Klammern holst du ein Element, negative Zahlen zählen von hinten. Mit start:stop bekommst du einen Ausschnitt als neue Liste, stop ist dabei nicht enthalten.',
    language: 'python',
    code: 'zahlen = [10, 20, 30, 40, 50]\n\nprint(zahlen[0])    # 10\nprint(zahlen[-1])   # 50\nprint(zahlen[1:3])  # [20, 30]',
    note: 'Der Index beginnt bei 0. Ein Index außerhalb der Liste führt zu einem IndexError.',
  },
  {
    slug: 'list-comprehension',
    topic: 'python',
    subtopic: 'listen',
    title: 'List Comprehension',
    summary: 'Eine neue Liste in einer Zeile aus einer anderen bauen.',
    explanation:
      'Eine List Comprehension ist eine kurze Schreibweise für eine for-Schleife, die eine neue Liste füllt. Mit if am Ende kommen nur passende Elemente hinein.',
    language: 'python',
    code: 'zahlen = [1, 2, 3, 4, 5]\n\nquadrate = [z * z for z in zahlen]\ngerade = [z for z in zahlen if z % 2 == 0]',
    note: 'Wird die Zeile lang oder verschachtelt, ist eine normale for-Schleife besser lesbar.',
  },
  {
    slug: 'def-return',
    topic: 'python',
    subtopic: 'funktionen',
    title: 'Funktionen mit def und return',
    summary: 'Code einmal schreiben und mit anderen Werten wiederverwenden.',
    explanation:
      'Mit def legst du eine Funktion an. Die Werte in den Klammern heißen Parameter, ein Parameter mit = hat einen Standardwert. return gibt das Ergebnis an die Stelle zurück, an der die Funktion aufgerufen wurde.',
    language: 'python',
    code: 'def brutto(netto, steuer=0.19):\n    return round(netto * (1 + steuer), 2)\n\nprint(brutto(100))        # 119.0\nprint(brutto(100, 0.07))  # 107.0',
    note: 'Ohne return gibt eine Funktion None zurück.',
  },

  {
    slug: 'dictionary-durchlaufen',
    topic: 'python',
    subtopic: 'dictionaries',
    title: 'Dictionary durchlaufen',
    summary: 'Schlüssel und Wert gemeinsam durchgehen.',
    explanation:
      '.items() liefert bei jedem Durchlauf ein Paar aus Schlüssel und Wert. Die for-Schleife verteilt es direkt auf zwei Variablen.',
    language: 'python',
    code: "user = {'name': 'Jens', 'role': 'dev'}\n\nfor key, value in user.items():\n    print(key, value)",
    note: 'Ohne .items() bekommst du nur die Schlüssel.',
  },
  {
    slug: 'f-strings',
    topic: 'python',
    subtopic: 'strings',
    title: 'f-Strings',
    summary: 'Variablen in Text einsetzen.',
    explanation:
      'Ein f vor den Anführungszeichen macht aus dem Text einen f-String. In geschweiften Klammern kann jede Variable oder Rechnung stehen.',
    language: 'python',
    code: "name = 'Jens'\nprint(f'Hallo {name}, du hast {3 + 2} Aufgaben.')",
  },

  // Django
  {
    slug: 'model-definieren',
    topic: 'django',
    subtopic: 'models-migrationen',
    title: 'Model definieren',
    summary: 'Eine Datenbanktabelle als Python-Klasse beschreiben.',
    explanation:
      'Jede Klasse, die von models.Model erbt, wird zu einer Tabelle. Jedes Feld der Klasse wird zu einer Spalte. Django legt die Spalte id automatisch an.',
    language: 'python',
    code: 'from django.db import models\n\n\nclass Task(models.Model):\n    title = models.CharField(max_length=200)\n    done = models.BooleanField(default=False)\n    created_at = models.DateTimeField(auto_now_add=True)',
    note: 'Nach jeder Änderung am Model: python manage.py makemigrations und danach python manage.py migrate.',
  },

  {
    slug: 'gitignore-fuer-django',
    topic: 'django',
    subtopic: 'projekt',
    title: '.gitignore für Django',
    summary: 'Was nicht ins Repository gehört.',
    explanation:
      'Die virtuelle Umgebung, Cache-Dateien, die lokale Datenbank und die .env bleiben auf deinem Rechner. Wer das Projekt klont, erzeugt sie selbst neu.',
    language: 'gitignore',
    code: 'env/\n__pycache__/\n*.pyc\ndb.sqlite3\n.env',
    note: 'Lege die .gitignore vor dem ersten Commit an. Was einmal auf GitHub liegt, bleibt in der Historie.',
  },

  // Django REST Framework
  {
    slug: 'model-serializer',
    topic: 'django-rest-framework',
    subtopic: 'serializer',
    title: 'ModelSerializer',
    summary: 'Ein Model in JSON umwandeln und eingehende Daten prüfen.',
    explanation:
      'Ein ModelSerializer baut die Felder aus deinem Model selbst auf. In der inneren Klasse Meta legst du fest, welches Model und welche Felder er verwendet.',
    language: 'python',
    code: "from rest_framework import serializers\n\nfrom .models import Task\n\n\nclass TaskSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = Task\n        fields = ['id', 'title', 'done', 'created_at']\n        read_only_fields = ['created_at']",
    note: "fields = '__all__' gibt auch Felder heraus, die du vielleicht nicht zeigen willst. Nenne die Felder lieber einzeln.",
  },

  {
    slug: 'viewset-und-router',
    topic: 'django-rest-framework',
    subtopic: 'views-viewsets',
    title: 'ViewSet und Router',
    summary: 'Alle Endpunkte für ein Model auf einmal.',
    explanation:
      'Ein ModelViewSet bringt Liste, Detail, Anlegen, Ändern und Löschen mit. Der Router erzeugt dazu die passenden URLs, zum Beispiel /tasks/ und /tasks/1/.',
    language: 'python',
    code: "# views.py\nfrom rest_framework import viewsets\n\nclass TaskViewSet(viewsets.ModelViewSet):\n    queryset = Task.objects.all()\n    serializer_class = TaskSerializer\n\n# urls.py\nfrom rest_framework.routers import DefaultRouter\n\nrouter = DefaultRouter()\nrouter.register('tasks', TaskViewSet)\nurlpatterns = router.urls",
  },
  {
    slug: 'login-per-token',
    topic: 'django-rest-framework',
    subtopic: 'authentifizierung',
    title: 'Login per Token',
    summary: 'Benutzer über einen Token erkennen.',
    explanation:
      'Nach migrate kann jeder Benutzer einen Token bekommen. Das Frontend schickt ihn bei jeder Anfrage im Header mit, und Django REST Framework erkennt daran den Benutzer.',
    language: 'python',
    code: "# settings.py\nINSTALLED_APPS += ['rest_framework.authtoken']\nREST_FRAMEWORK = {\n    'DEFAULT_AUTHENTICATION_CLASSES': [\n        'rest_framework.authentication.TokenAuthentication',\n    ],\n}",
    note: 'Der Header sieht so aus: Authorization: Token <dein-token>',
  },
  {
    slug: 'cors-erlauben',
    topic: 'django-rest-framework',
    subtopic: 'cors',
    title: 'CORS für das Frontend erlauben',
    summary: 'Anfragen vom Angular-Frontend zulassen.',
    explanation:
      'Der Browser blockiert Anfragen von localhost:4200 an localhost:8000, solange das Backend sie nicht ausdrücklich erlaubt. Das Paket django-cors-headers setzt dafür die nötigen Header.',
    language: 'python',
    code: "pip install django-cors-headers\n\n# settings.py\nINSTALLED_APPS += ['corsheaders']\nMIDDLEWARE = ['corsheaders.middleware.CorsMiddleware'] + MIDDLEWARE\nCORS_ALLOWED_ORIGINS = ['http://localhost:4200']",
    note: 'Die CorsMiddleware muss möglichst weit oben in MIDDLEWARE stehen.',
  },

  // Git
  {
    slug: 'branch-anlegen',
    topic: 'git',
    subtopic: 'branches',
    title: 'Mit einem Branch arbeiten',
    summary: 'An einem Feature arbeiten, ohne main zu verändern.',
    explanation:
      'Ein Branch ist ein eigener Entwicklungszweig. Du legst ihn an, speicherst dort deine Commits und schickst ihn zu GitHub. Über einen Pull Request kommt er später in main.',
    language: 'terminal',
    code: 'git switch -c feat/login\ngit add .\ngit commit -m "feat: add login form"\ngit push -u origin feat/login',
    note: 'Wechsle vor dem neuen Branch auf main und führe git pull aus, sonst fehlen dir neue Änderungen.',
  },
];

@Service()
export class ConceptApi {
  getByTopic(topic: string): Observable<Concept[]> {
    return of(CONCEPTS.filter((concept) => concept.topic === topic));
  }

  getSummary(): Observable<{ entries: number; topics: number }> {
    return of({
      entries: CONCEPTS.length,
      topics: new Set(CONCEPTS.map((concept) => concept.topic)).size,
    });
  }
}
